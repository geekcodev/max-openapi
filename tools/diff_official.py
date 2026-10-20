#!/usr/bin/env python3
"""Сверка с официальной `schema.yaml`: пути, операции, схемы, поля и `required`,
параметры, `responses`, битые ссылки.

Живёт в репозитории (`tools/`); запускается напрямую или через
`tools/check_spec.py` (см. AGENTS.md § 7.1).

Использование:
    python3 tools/diff_official.py [наша_спека] [официальная_спека]

Официальная спека по умолчанию — `$OFFICIAL_SCHEMA` или
`/tmp/opencode/max-official/schema.yaml` (клон `api-schema`).
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import DEFAULT_OFF, DEFAULT_OUR, METHODS, load, merge  # noqa: E402

SECTIONS = (
    "1. ПУТИ",
    "2. ОПЕРАЦИИ",
    "3. СХЕМЫ (имена)",
    "4. ПОЛЯ И required (симметрично, allOf/$ref развёрнуты)",
    "5. ПАРАМЕТРЫ components/parameters",
    "6. ОТВЕТЫ components/responses",
    "7. БИТЫЕ ССЫЛКИ в нашей спеке",
)

KIND_LABEL = {
    "missing_path": "нет у нас",
    "extra_path": "лишние у нас",
    "missing_op": "нет у нас",
    "extra_op": "лишние у нас",
    "missing_schema": "нет у нас",
    "extra_schema": "лишние у нас",
    "missing_field": "поля нет у нас",
    "extra_field": "лишнее поле у нас",
    "missing_required": "required нет у нас",
    "extra_required": "лишний required у нас",
    "missing_param": "нет у нас",
    "extra_param": "лишние у нас",
    "missing_response": "нет у нас",
    "extra_response": "лишние у нас",
    "broken_ref": "битые ссылки",
}

# Порядок вывода внутри секции (для «плоских» секций без групп).
SECTION_KINDS = {
    SECTIONS[0]: ["missing_path", "extra_path"],
    SECTIONS[1]: ["missing_op", "extra_op"],
    SECTIONS[2]: ["missing_schema", "extra_schema"],
    SECTIONS[4]: ["missing_param", "extra_param"],
    SECTIONS[5]: ["missing_response", "extra_response"],
    SECTIONS[6]: ["broken_ref"],
}
FIELD_KINDS = ["missing_field", "extra_field", "missing_required", "extra_required"]

WIDE = {  # значения перечисляем через запятую, а не repr(list)
    "missing_schema", "extra_schema", "missing_op", "extra_op",
    "missing_path", "extra_path", "missing_param", "extra_param",
    "missing_response", "extra_response",
}


def _f(section, kind, key, group=None):
    return {"tool": "official", "section": section, "kind": kind, "key": key, "group": group}


def _info(section, text):
    return {"tool": "official", "section": section, "kind": "info", "key": None,
            "group": None, "text": text}


def ops(doc):
    return {(p, m) for p, mm in (doc.get("paths") or {}).items() for m in mm if m in METHODS}


def collect(our, off, our_path=None):
    out = []
    # 1. пути
    p_our, p_off = set(our.get("paths") or {}), set(off.get("paths") or {})
    out += [_f(SECTIONS[0], "missing_path", x) for x in sorted(p_off - p_our)]
    out += [_f(SECTIONS[0], "extra_path", x) for x in sorted(p_our - p_off)]
    # 2. операции
    o_our, o_off = ops(our), ops(off)
    out += [_f(SECTIONS[1], "missing_op", f"{m.upper()} {p}") for p, m in sorted(o_off - o_our)]
    out += [_f(SECTIONS[1], "extra_op", f"{m.upper()} {p}") for p, m in sorted(o_our - o_off)]
    out.append(_info(SECTIONS[1], f"  всего: официально {len(o_off)}, у нас {len(o_our)}"))
    # 3. имена схем
    s_our = our["components"]["schemas"]
    s_off = off["components"]["schemas"]
    out.append(_info(SECTIONS[2], f"  официально {len(s_off)}, у нас {len(s_our)}"))
    out += [_f(SECTIONS[2], "missing_schema", x) for x in sorted(set(s_off) - set(s_our))]
    out += [_f(SECTIONS[2], "extra_schema", x) for x in sorted(set(s_our) - set(s_off))]
    # 4. поля и required
    for name in sorted(set(s_our) & set(s_off)):
        a, b = merge(s_our[name], our), merge(s_off[name], off)
        pa, pb = set(a["properties"]), set(b["properties"])
        if not pa and not pb:
            continue
        for field in sorted(pb - pa):
            out.append(_f(SECTIONS[3], "missing_field", f"{name}.{field}", group=name))
        for field in sorted(pa - pb):
            out.append(_f(SECTIONS[3], "extra_field", f"{name}.{field}", group=name))
        for field in sorted(b["required"] - a["required"]):
            out.append(_f(SECTIONS[3], "missing_required", f"{name}.{field}", group=name))
        for field in sorted(a["required"] - b["required"]):
            out.append(_f(SECTIONS[3], "extra_required", f"{name}.{field}", group=name))
    # 5. параметры
    q_our = set((our.get("components") or {}).get("parameters") or {})
    q_off = set((off.get("components") or {}).get("parameters") or {})
    out += [_f(SECTIONS[4], "missing_param", x) for x in sorted(q_off - q_our)]
    out += [_f(SECTIONS[4], "extra_param", x) for x in sorted(q_our - q_off)]
    # 6. responses
    r_our = set((our.get("components") or {}).get("responses") or {})
    r_off = set((off.get("components") or {}).get("responses") or {})
    out += [_f(SECTIONS[5], "missing_response", x) for x in sorted(r_off - r_our)]
    out += [_f(SECTIONS[5], "extra_response", x) for x in sorted(r_our - r_off)]
    # 7. битые ссылки
    if our_path:
        text = open(our_path, encoding="utf-8").read()
        for target, name in re.findall(r'"#/components/(schemas|responses|parameters)/(\w+)"', text):
            if name not in (our.get("components") or {}).get(target, {}):
                out.append(_f(SECTIONS[6], "broken_ref", f"{target}/{name}"))
    return out


def _fmt(kind, vals):
    if not vals:
        return "—"
    return ", ".join(vals) if kind in WIDE else repr(vals)


def report(findings):
    for section in SECTIONS:
        items = [f for f in findings if f["section"] == section]
        print("=" * 70)
        print(section)
        for f in items:
            if f["kind"] == "info":
                print(f["text"])
        body = [f for f in items if f["kind"] != "info"]
        groups = []
        for f in body:
            if f["group"] not in groups:
                groups.append(f["group"])
        if groups and groups != [None]:
            for group in groups:
                print(f"  {group}:")
                here = [f for f in body if f["group"] == group]
                for kind in FIELD_KINDS:
                    vals = sorted(f["key"].split(".", 1)[1] for f in here if f["kind"] == kind)
                    if vals:
                        print(f"    {KIND_LABEL[kind]}: {_fmt(kind, vals)}")
        else:
            kinds = SECTION_KINDS.get(section, sorted({f["kind"] for f in body}))
            for kind in kinds:
                vals = sorted(f["key"] for f in body if f["kind"] == kind)
                print(f"  {KIND_LABEL[kind]}: {_fmt(kind, vals)}")
    print()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    our_path = argv[0] if len(argv) > 0 else DEFAULT_OUR
    off_path = argv[1] if len(argv) > 1 else DEFAULT_OFF
    report(collect(load(our_path), load(off_path), our_path))


if __name__ == "__main__":
    main()
