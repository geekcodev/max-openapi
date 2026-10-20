#!/usr/bin/env python3
"""Единая проверка спецификации: валидация (AGENTS.md § 7) + машинная сверка (§ 7.1).

Прогоняет:

1. валидацию `openapi.yaml` — синтаксис YAML, дубли ключей, разрешение `$ref`,
   строгую проверку OpenAPI 3.1.0 (`openapi-spec-validator`, если установлен);
2. сверку **отметки версии** `info.x-official-schema` с `info.version` официальной
   схемы (`version` — жёсткая проверка, `commit` — справочно, см. AGENTS.md § 7.1);
3. три компаратора (`diff_official.py`, `types_diff.py`, `op_bodies_diff.py`) —
   их полные отчёты печатаются целиком;
4. сверку найденного с **реестром зарегистрированных отклонений**: зарегистрированные
   отделяются от новых, а запись реестра, под которую ничего не нашлось, помечается
   как устаревшая.

Запуск:
    python3 tools/check_spec.py
    python3 tools/check_spec.py --our openapi.yaml --official /tmp/opencode/max-official/schema.yaml
    OFFICIAL_SCHEMA=/path/schema.yaml python3 tools/check_spec.py

Код возврата: 0 — только зарегистрированные отклонения; 1 — есть новые или устарела
отметка версии; 2 — сбой проверок или нет официальной схемы.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diff_official  # noqa: E402
import op_bodies_diff  # noqa: E402
import types_diff  # noqa: E402
import yaml  # noqa: E402
from _common import DEFAULT_OFF, DEFAULT_OUR  # noqa: E402

# --- Реестр зарегистрированных отклонений -------------------------------------
# Каждая запись: (компаратор, вид, ключи или None, где зарегистрировано).
# None в «ключах» — вид зарегистрирован целиком (группа разобрана в доке).
# Новое отклонение, не попавшее сюда, — это сигнал: либо правка спеки, либо
# регистрация в AGENTS.md § 2.1 / § 5 (см. AGENTS.md § 7.1).
REGISTERED = [
    ("official", "missing_schema", None,
     "DOCS_MAP § 1 — 40 отсутствующих схем разобраны по группам"),
    ("official", "extra_schema", None,
     "DOCS_MAP § 1 — наши базы/enum/обёртки/payload-подтипы"),
    ("official", "extra_param", None,
     "AGENTS § 7.1 п. 1 — параметры вынесены в components/parameters"),
    ("official", "missing_response", None,
     "AGENTS § 5 — спека использует единый список кодов"),
    ("official", "extra_response", None,
     "AGENTS § 5 — спека использует единый список кодов"),
    ("official", "extra_field", {
        "BotInfo.name", "ChatMember.name", "User.name", "UserWithPhoto.name"},
     "AGENTS § 2.1 — User.name (deprecated в текстовой доке, нет в schema.yaml)"),
    ("official", "extra_field", {"UploadedInfo.url"},
     "AGENTS § 2.1 — url payload вложений; ответ POST /uploads — UploadEndpoint"),
    # Расположение метаданных вложений внутри payload (AGENTS.md § 2.1).
    ("official", "missing_field", {
        "AudioAttachment.transcription",
        "FileAttachment.filename", "FileAttachment.size",
        "ShareAttachment.description", "ShareAttachment.image_url", "ShareAttachment.title",
        "StickerAttachment.height", "StickerAttachment.width",
        "VideoAttachment.duration", "VideoAttachment.height", "VideoAttachment.thumbnail",
        "VideoAttachment.width"},
     "AGENTS § 2.1 — метаданные вложений лежат в payload, а не на верхнем уровне"),
    ("official", "extra_field", {
        "FileAttachmentPayload.filename", "FileAttachmentPayload.size",
        "ShareAttachmentPayload.description", "ShareAttachmentPayload.image_url",
        "ShareAttachmentPayload.title",
        "StickerAttachmentPayload.height", "StickerAttachmentPayload.width"},
     "AGENTS § 2.1 — метаданные вложений лежат в payload, а не на верхнем уровне"),
    ("official", "missing_required", {
        "FileAttachment.filename", "FileAttachment.size",
        "StickerAttachment.height", "StickerAttachment.width"},
     "AGENTS § 2.1 — тот же перенос метаданных вложений"),
    ("official", "extra_required", {
        "FileAttachmentPayload.filename", "FileAttachmentPayload.size",
        "StickerAttachmentPayload.height", "StickerAttachmentPayload.width"},
     "AGENTS § 2.1 — тот же перенос метаданных вложений"),
    ("types", "nullability", {
        "Message.body"},
     "AGENTS § 2.1 — обязателен, но nullable (текстовая дока допускает body: null)"),
    ("types", "nullability", {
        "UserRemovedFromChatUpdate.admin_id"},
     "AGENTS § 5 — schema.yaml не-nullable, но описание допускает null"),
    ("types", "type", {
        "CommentCreatedUpdate.message", "CommentEditedUpdate.message"},
     "AGENTS § 2.1 — событие несёт CommentMessage, официальная схема ссылается на Message"),
    ("bodies", "extra_field", {"POST /chats/{chatId}/members/admins::marker"},
     "AGENTS § 5 — страница метода документирует marker, машинная схема нет"),
    ("bodies", "extra_field", {"GET /chats/{chatId}/members/me::name", "GET /me::name"},
     "AGENTS § 2.1 — User.name"),
]

IGNORED_KINDS = {"info", "type_noise", "enum_order"}


def registered(tool, kind, key):
    """Возвращает причину регистрации или None, если отклонение новое."""
    for reg_tool, reg_kind, keys, why in REGISTERED:
        if reg_tool == tool and reg_kind == kind and (keys is None or key in keys):
            return why
    return None


# --- Валидация -----------------------------------------------------------------


class _DupLoader(yaml.SafeLoader):
    pass


def _no_dups(loader, node, deep=False):
    keys = []
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in keys:
            raise ValueError(f"дубль ключа {key!r} (строка {key_node.start_mark.line + 1})")
        keys.append(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dups)

STRICT_CODE = (
    "from openapi_spec_validator import validate\n"
    "from openapi_spec_validator.readers import read_from_filename\n"
    "spec, _ = read_from_filename({path!r})\n"
    "validate(spec)\n"
    "print('ok')\n"
)


def strict_oas(path):
    """Строгая проверка 3.1.0: импорт в текущем интерпретаторе или в известном venv."""
    candidates = [os.environ.get("OAS_PYTHON"), sys.executable,
                  "/tmp/opencode/.venv-oas/bin/python"]
    for py in candidates:
        if not py or not os.path.exists(py):
            continue
        proc = subprocess.run([py, "-c", STRICT_CODE.format(path=os.path.abspath(path))],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            return True, f"валидна ({py})"
        if "No module named" in proc.stderr:
            continue
        tail = (proc.stderr.strip().splitlines() or ["неизвестная ошибка"])[-1]
        return False, tail
    return None, ("пропущено: нет `openapi-spec-validator` "
                  "(`pip install openapi-spec-validator` или `OAS_PYTHON=...`)")


def validate(our_path):
    """Возвращает (строки отчёта, всё_ок)."""
    lines, ok = [], True
    try:
        text = open(our_path, encoding="utf-8").read()
        spec = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        return [f"  YAML-синтаксис: ОШИБКА — {exc}"], False
    lines.append("  YAML-синтаксис: OK")
    try:
        yaml.load(text, Loader=_DupLoader)
        lines.append("  дубли ключей YAML: нет")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"  дубли ключей YAML: ОШИБКА — {exc}")
        ok = False
    refs = re.findall(r'"#/components/(schemas|responses|parameters)/(\w+)"', text)
    broken = sorted({f"{t}/{n}" for t, n in refs
                     if n not in (spec.get("components") or {}).get(t, {})})
    parts = [f"схемы/ответы {sum(1 for t, _ in refs if t != 'parameters')}",
             f"параметры {sum(1 for t, _ in refs if t == 'parameters')}"]
    if broken:
        lines.append(f"  $ref: {len(refs)} ссылок ({', '.join(parts)}), БИТЫЕ — {broken}")
        ok = False
    else:
        lines.append(f"  $ref: {len(refs)} ссылок ({', '.join(parts)}), битых нет")
    strict, note = strict_oas(our_path)
    lines.append(f"  OpenAPI 3.1.0: {note}")
    if strict is False:
        ok = False
    return lines, ok


# --- Сверка версии официальной схемы -------------------------------------------


def official_commit(path):
    """Короткий SHA официального клона (справочно); None, если определить не удалось."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        proc = subprocess.run(["git", "-C", directory, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True)
    except OSError:
        return None
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and sha else None


def version_check(our, off, official_path):
    """Сверяет `info.x-official-schema` нашей спеки с `info.version` официальной.

    `version` — жёсткая проверка (расхождение = код возврата 1); `commit`/`verified`
    — справочно, на код возврата не влияют (см. AGENTS.md § 7.1). Возвращает
    (строки отчёта, всё_ок).
    """
    marker = (our.get("info") or {}).get("x-official-schema") or {}
    off_version = str((off.get("info") or {}).get("version", "") or "")
    if not marker:
        return ["  метка `info.x-official-schema`: ОТСУТСТВУЕТ "
                "(добавьте, см. AGENTS.md § 7.1)"], True
    our_version = str(marker.get("version", "") or "")
    lines = [
        f"  наша отметка: {our_version or '—'} "
        f"(коммит {marker.get('commit', '—')}, сверено {marker.get('verified', '—')})",
        f"  официальная схема: {off_version or '—'}",
    ]
    ok = our_version == off_version
    lines.append("  версия: совпадает" if ok else
                 f"  версия: РАСХОЖДЕНИЕ — официальная схема обновилась "
                 f"({off_version}), нужна сверка и правка отметки")
    sha = official_commit(official_path)
    if sha:
        note = "" if marker.get("commit") == sha else f" (в отметке {marker.get('commit', '—')})"
        lines.append(f"  коммит официального клона: {sha}{note}")
    return lines, ok


# --- Сверка --------------------------------------------------------------------


def flatten(our, off, our_path):
    return {
        "official": diff_official.collect(our, off, our_path=our_path),
        "types": types_diff.collect(our, off),
        "bodies": op_bodies_diff.collect(our, off),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Проверка openapi.yaml: валидация + сверка")
    parser.add_argument("--our", default=DEFAULT_OUR, help="наша спека")
    parser.add_argument("--official", default=DEFAULT_OFF, help="официальная schema.yaml")
    parser.add_argument("--verbose", action="store_true",
                        help="показать все ключи зарегистрированных отклонений")
    args = parser.parse_args(argv)

    print("== ВАЛИДАЦИЯ ==")
    valid_lines, valid_ok = validate(args.our)
    print("\n".join(valid_lines))

    if not os.path.exists(args.official):
        print(f"\nОфициальная схема не найдена: {args.official}")
        print("Клонируйте: git clone --depth 1 "
              "https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official")
        return 2

    our, off = yaml.safe_load(open(args.our, encoding="utf-8")), yaml.safe_load(open(args.official, encoding="utf-8"))
    findings = flatten(our, off, args.our)

    print("\n== ВЕРСИЯ ОФИЦИАЛЬНОЙ СХЕМЫ ==")
    version_lines, version_ok = version_check(our, off, args.official)
    print("\n".join(version_lines))

    print()
    for tool, name in (("official", "diff_official.py"), ("types", "types_diff.py"),
                       ("bodies", "op_bodies_diff.py")):
        print(f"########## {name} ##########")
        {"official": diff_official.report, "types": types_diff.report,
         "bodies": op_bodies_diff.report}[tool](findings[tool])

    matched, new = [], []
    for tool, items in findings.items():
        for f in items:
            if f["kind"] in IGNORED_KINDS:
                continue
            why = registered(tool, f["kind"], f["key"])
            if why is None:
                new.append((tool, f))
            else:
                matched.append((tool, f, why))

    groups = {}
    for tool, f, why in matched:
        groups.setdefault((tool, f["kind"], why), []).append(f["key"])

    print("== ИТОГ СВЕРКИ ==")
    print(f"  зарегистрированных отклонений: {len(matched)} "
          f"(групп: {len(groups)})")

    if args.verbose:
        for (tool, kind, why), keys in sorted(groups.items()):
            print(f"    [{tool}] {kind} — {len(keys)}: {sorted(keys)}")
            print(f"        {why}")
    else:
        for (tool, kind, why), keys in sorted(groups.items()):
            print(f"    [{tool}] {kind} — {len(keys)}: {why}")
        print("    (полный список ключей — `--verbose`)")

    matched_pairs = {(tool, f["kind"], f["key"]) for tool, f, _ in matched}
    stale = []
    for reg_tool, reg_kind, keys, _ in REGISTERED:
        if keys is None:
            continue
        missing = sorted(k for k in keys if (reg_tool, reg_kind, k) not in matched_pairs)
        if missing:
            stale.append((reg_tool, reg_kind, missing))
    if stale:
        print("\n  реестр: записи без совпадений (проверьте, не устарели ли):")
        for reg_tool, reg_kind, missing in stale:
            print(f"    [{reg_tool}] {reg_kind}: {missing}")

    if new:
        print(f"\n  НОВЫХ РАСХОЖДЕНИЙ: {len(new)} — закройте правкой спеки "
              f"или строкой в AGENTS.md § 2.1 / § 5:")
        for tool, f in sorted(new, key=lambda x: (x[0], x[1]["key"] or "")):
            print(f"    [{tool}] {f['kind']} {f['key']}")
    else:
        print("\n  новых расхождений нет")

    print("\n  итог: " + ("расхождения только зарегистрированные" if not new
                          else f"есть незарегистрированные ({len(new)})")
          + ("" if version_ok else "; отметка версии устарела"))
    if not valid_ok:
        return 2
    return 1 if (new or not version_ok) else 0


if __name__ == "__main__":
    sys.exit(main())
