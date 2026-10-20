#!/usr/bin/env python3
"""Сверка тел запросов и 2xx-ответов **по смыслу**, а не по именам схем.

Официальная спека ссылается на именованные обёртки (`ChatAdminsList`,
`SendMessageResult`…), у нас те же данные часто записаны инлайн — сверка имён
этого не видит. Здесь обе стороны разворачиваются в плоский набор полей и
`required` и сравниваются без учёта имён схем. Именно он видит то, что не видит
`diff_official.py` (см. AGENTS.md § 7.1).

Использование:
    python3 tools/op_bodies_diff.py [наша_спека] [официальная_спека]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import DEFAULT_OFF, DEFAULT_OUR, METHODS, deref, load, merge  # noqa: E402

BODY = "ТЕЛА ЗАПРОСОВ"
RESP = "2xx-ОТВЕТЫ"


def _f(section, kind, key, group):
    return {"tool": "bodies", "section": section, "kind": kind, "key": key, "group": group}


def body_schema(op, doc):
    rb = deref(op.get("requestBody") or {}, doc)
    return (rb.get("content") or {}).get("application/json", {}).get("schema")


def ok_schema(op, doc):
    for code, resp in (op.get("responses") or {}).items():
        if str(code).startswith("2"):
            resp = deref(resp, doc)
            return (resp.get("content") or {}).get("application/json", {}).get("schema")
    return None


def _flat(schema, doc):
    if not schema:
        return set(), set()
    m = merge(schema, doc)
    return set(m["properties"]), m["required"]


def collect(our, off):
    out = []
    for section, picker in ((BODY, body_schema), (RESP, ok_schema)):
        for path, ops in sorted((off.get("paths") or {}).items()):
            for method, off_op in ops.items():
                if method not in METHODS:
                    continue
                our_op = ((our.get("paths") or {}).get(path) or {}).get(method)
                if not our_op:
                    continue
                off_schema, our_schema = picker(off_op, off), picker(our_op, our)
                if off_schema is None and our_schema is None:
                    continue
                po, ro = _flat(off_schema, off)
                py, ry = _flat(our_schema, our)
                if po == py and ro == ry:
                    continue
                op = f"{method.upper()} {path}"
                for field in sorted(py - po):
                    out.append(_f(section, "extra_field", f"{op}::{field}", op))
                for field in sorted(po - py):
                    out.append(_f(section, "missing_field", f"{op}::{field}", op))
                for field in sorted(ry - ro):
                    out.append(_f(section, "extra_required", f"{op}::{field}", op))
                for field in sorted(ro - ry):
                    out.append(_f(section, "missing_required", f"{op}::{field}", op))
    return out


LABEL = {
    "extra_field": "лишние поля у нас",
    "missing_field": "полей нет у нас",
    "extra_required": "лишний required у нас",
    "missing_required": "required нет у нас",
}
ORDER = ["extra_field", "missing_field", "extra_required", "missing_required"]


def report(findings):
    for section in (BODY, RESP):
        print(f"== {section} ==")
        items = [f for f in findings if f["section"] == section]
        groups = []
        for f in items:
            if f["group"] not in groups:
                groups.append(f["group"])
        for group in groups:
            print(f"  {group}")
            for kind in ORDER:
                vals = sorted(f["key"].split("::", 1)[1] for f in items
                              if f["group"] == group and f["kind"] == kind)
                if vals:
                    print(f"        {LABEL[kind]}: {vals}")
        if not groups:
            print("  —")
        print()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    our_path = argv[0] if len(argv) > 0 else DEFAULT_OUR
    off_path = argv[1] if len(argv) > 1 else DEFAULT_OFF
    report(collect(load(our_path), load(off_path)))


if __name__ == "__main__":
    main()
