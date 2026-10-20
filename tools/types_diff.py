#!/usr/bin/env python3
"""Сверка типов / nullability / enum с официальной `schema.yaml`.

Разворачивает `$ref` и `allOf` с обеих сторон; nullability читается и в форме
OpenAPI 3.1 (`type: [x, "null"]`, `anyOf` с `{type: "null"}`), и в форме
официальной 3.0 (`nullable: true`).

Совместимые формы записи отделены от настоящих расхождений: строки «шум»
(псевдонимы скаляров, `format: uri`, `null+ref` как запись nullable, пара
`*AttachmentPayload`) помечены семейством и в зачёт расхождений не идут.
Расхождением считается только несовпадение `ref:`↔`ref:` двух разных схем
(`family = real`) — см. AGENTS.md § 7.1.

Использование:
    python3 tools/types_diff.py [наша_спека] [официальная_спека]
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import DEFAULT_OFF, DEFAULT_OUR, deref, deref_all, load  # noqa: E402

OUT_TYPES = "ТИПЫ"
OUT_NULL = "NULLABILITY"
OUT_ENUM = "ENUM"

SCALAR_RE = re.compile(r"^(integer|number|string|boolean|object|any)(/|$)")

# Сознательные пары `ref:`↔`ref:` (payload вложений и клавиатура, AGENTS.md § 2.1).
REF_PAIRS = {
    frozenset({"ref:MediaAttachmentPayload", "ref:AudioAttachmentPayload"}),
    frozenset({"ref:MediaAttachmentPayload", "ref:VideoAttachmentPayload"}),
    frozenset({"ref:Keyboard", "ref:InlineKeyboardAttachmentPayload"}),
    frozenset({"ref:InlineKeyboardAttachmentRequestPayload", "ref:InlineKeyboardAttachmentPayload"}),
}


def _f(section, kind, key, text, family=None):
    return {"tool": "types", "section": section, "kind": kind, "key": key,
            "text": text, "group": None, "family": family}


def props_of(name, doc):
    """Собирает `properties` из `allOf`-цепочки схемы."""
    out = {}
    for sub in deref_all(doc["components"]["schemas"][name], doc):
        out.update(sub.get("properties") or {})
    return out


def shallow_kind(schema, doc):
    """Тип «как записан»: `ref:Имя`, `integer/int64`, `null+ref:Имя`, …"""
    if isinstance(schema, dict) and "$ref" in schema:
        return "ref:" + schema["$ref"].split("/")[-1]
    schema = deref(schema, doc)
    if not isinstance(schema, dict):
        return "any"
    if "type" in schema:
        types = schema["type"]
        types = [types] if isinstance(types, str) else list(types)
        base = "/".join(sorted(x for x in types if x != "null"))
        if "format" in schema:
            base = f"{base}/{schema['format']}"
        return base or "null"
    for key in ("allOf", "anyOf", "oneOf"):
        if schema.get(key):
            kinds = {shallow_kind(x, doc) for x in schema[key]}
            kinds.discard("any")
            return kinds.pop() if len(kinds) == 1 else ("+".join(sorted(kinds)) or "any")
    return "any"


def nullable(schema, doc, depth=0):
    schema = deref(schema, doc)
    if not isinstance(schema, dict) or depth > 20:
        return False
    if schema.get("nullable") is True:
        return True
    types = schema.get("type")
    if types == "null" or (isinstance(types, list) and "null" in types):
        return True
    for key in ("allOf", "anyOf", "oneOf"):
        for sub in schema.get(key) or []:
            if nullable(sub, doc, depth + 1):
                return True
    return False


def enum_of(schema, doc, depth=0):
    schema = deref(schema, doc)
    if not isinstance(schema, dict) or depth > 20:
        return None
    if "enum" in schema:
        return list(schema["enum"])
    for key in ("allOf", "anyOf", "oneOf"):
        for sub in schema.get(key) or []:
            found = enum_of(sub, doc, depth + 1)
            if found:
                return found
    return None


def classify(off_kind, our_kind):
    """Семейство расхождения «как записан тип»: шум или настоящее (real)."""
    if "null+" in off_kind or "null+" in our_kind:
        return "null_form"
    if off_kind.replace("/uri", "") == our_kind.replace("/uri", ""):
        return "format_uri"
    if frozenset({off_kind, our_kind}) in REF_PAIRS:
        return "payload_relocation"
    if SCALAR_RE.match(off_kind) or SCALAR_RE.match(our_kind):
        return "alias"
    return "real"


def collect(our, off):
    out = []
    s_our, s_off = our["components"]["schemas"], off["components"]["schemas"]
    for name in sorted(set(s_our) & set(s_off)):
        pa, pb = props_of(name, our), props_of(name, off)
        for prop in sorted(set(pa) & set(pb)):
            ka, kb = shallow_kind(pa[prop], our), shallow_kind(pb[prop], off)
            if ka != kb:
                family = classify(kb, ka)
                out.append(_f(OUT_TYPES, "type" if family == "real" else "type_noise",
                              f"{name}.{prop}", f"офиц[{kb}] vs у нас[{ka}]", family))
            na, nb = nullable(pa[prop], our), nullable(pb[prop], off)
            if na != nb:
                out.append(_f(OUT_NULL, "nullability", f"{name}.{prop}",
                              f'офиц {"nullable" if nb else "обязательное"}, '
                              f'у нас {"nullable" if na else "не nullable"}'))
            ea, eb = enum_of(pa[prop], our), enum_of(pb[prop], off)
            if ea is not None and eb is not None and ea != eb:
                order = "порядок значений" if sorted(ea) == sorted(eb) else "РАЗНЫЕ ЗНАЧЕНИЯ"
                out.append(_f(OUT_ENUM, "enum_order" if order == "порядок значений" else "enum",
                              f"{name}.{prop}", f"офиц={eb} у нас={ea} ({order})"))
    out.append(_f(OUT_TYPES, "info", None, summary(out)))
    return out


def summary(findings):
    noise = sum(1 for f in findings if f["kind"] == "type_noise")
    nulls = sum(1 for f in findings if f["kind"] == "nullability")
    enums = sum(1 for f in findings if f["kind"] == "enum")
    real_types = sum(1 for f in findings if f["kind"] == "type")
    return (f"  Итого: типовых-шум {noise}, типовых-расхождений {real_types}, "
            f"nullability {nulls}, enum {enums} (порядок значений — не расхождение)")


def report(findings):
    noise = [f for f in findings if f["kind"] == "type_noise"]
    real = [f for f in findings if f["kind"] == "type"]
    print("== ТИПЫ (шум ref/format/allOf; настоящие расхождения — ниже) ==")
    for f in noise:
        print(f"  {f['key']}: {f['text']}  [{f['family']}]")
    if not noise:
        print("  —")
    print("\n== ТИПЫ — РАСХОЖДЕНИЯ (не шум) ==")
    for f in real:
        print(f"  {f['key']}: {f['text']}")
    if not real:
        print("  —")
    print("\n== NULLABILITY ==")
    for f in findings:
        if f["kind"] == "nullability":
            print(f"  {f['key']}: {f['text']}")
    if not any(f["kind"] == "nullability" for f in findings):
        print("  —")
    print("\n== ENUM ==")
    for f in findings:
        if f["kind"] in ("enum", "enum_order"):
            print(f"  {f['key']}: {f['text']}")
    if not any(f["kind"] in ("enum", "enum_order") for f in findings):
        print("  —")
    print("\n" + summary(findings))
    print()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    our_path = argv[0] if len(argv) > 0 else DEFAULT_OUR
    off_path = argv[1] if len(argv) > 1 else DEFAULT_OFF
    report(collect(load(our_path), load(off_path)))


if __name__ == "__main__":
    main()
