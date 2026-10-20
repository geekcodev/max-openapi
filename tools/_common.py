#!/usr/bin/env python3
"""Общие помощники компараторов (см. AGENTS.md § 7.1).

Компараторы разворачивают `$ref` и `allOf` **симметрично с обеих сторон**: имена
схем в официальной `schema.yaml` не совпадают с нашими (обёртки запросов, базы
`allOf`, псевдонимы скаляров вида `ChatId`), поэтому сравнение идёт по составу
полей, а не по именам схем.
"""
from __future__ import annotations

import os

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUR = os.path.join(REPO_ROOT, "openapi.yaml")
# Клон https://github.com/max-messenger/api-schema (см. AGENTS.md § 7.1);
# путь можно переопределить переменной окружения OFFICIAL_SCHEMA.
DEFAULT_OFF = os.environ.get("OFFICIAL_SCHEMA", "/tmp/opencode/max-official/schema.yaml")

METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ptr(doc, ref):
    cur = doc
    for part in ref[2:].split("/"):
        cur = cur[part.replace("~1", "/").replace("~0", "~")]
    return cur


def deref(schema, doc, depth=0):
    while isinstance(schema, dict) and "$ref" in schema and len(schema) == 1 and depth < 20:
        schema = ptr(doc, schema["$ref"])
        depth += 1
    return schema


def merge(schema, doc, depth=0):
    """Разворачивает цепочку `allOf`/`$ref` → `{'properties': {...}, 'required': set}`."""
    schema = deref(schema, doc, depth)
    props, req = {}, set()
    if not isinstance(schema, dict) or depth > 20:
        return {"properties": props, "required": req}
    for sub in schema.get("allOf") or []:
        m = merge(sub, doc, depth + 1)
        props.update(m["properties"])
        req |= m["required"]
    props.update(schema.get("properties") or {})
    req |= set(schema.get("required") or [])
    return {"properties": props, "required": req}


def deref_all(schema, doc, depth=0):
    """Разворачивает `allOf` в плоский список подсхем (без ключа `allOf`)."""
    schema = deref(schema, doc)
    if not isinstance(schema, dict) or depth > 20:
        return []
    res = [{k: v for k, v in schema.items() if k != "allOf"}]
    for sub in schema.get("allOf") or []:
        res.extend(deref_all(sub, doc, depth + 1))
    return res
