---
tags: [ openapi, docs, validation, fix, answers, uploads, comparators ]
date: 2026-10-20
---

# Сверка тел запросов и ответов «по смыслу» (расхождения вне имён схем)

## Проблема

Компаратор `diff_official.py` сверяет **имена** схем. Официальная спека ссылается на именованные обёртки
(`SendMessageResult`, `MessageList`, `ChatAdminsList`, `CallbackAnswer`…), у нас те же данные записаны инлайн в
операциях — поэтому расхождения внутри тел запросов и 2xx-ответов по имени невидимы. Проверка по смыслу (плоский набор
полей и `required` с разворачиванием `allOf`/`$ref`) выявила 2 реальных расхождения и 8 отсутствующих `required`.

## Решение

Новый компаратор `/tmp/opencode/op_bodies_diff.py` (живёт вне репозитория, описан в `AGENTS.md` § 7.1): сравнивает
`schema` тел запросов и 2xx-ответов каждой операции, не учитывая имена схем.

Правки `openapi.yaml` (2026-10-20):

- `POST /answers` — добавлено поле `notification` (string, nullable). Официальная `CallbackAnswer` = `{message,
  notification}`; на странице метода поле не отрендерено, но проза подтверждает («может обновить текущее сообщение
  **и/или** отправить одноразовое уведомление») — занесено в `AGENTS.md` § 5.
- Новая схема `UploadEndpoint` (`url` — `required`, `token` — nullable) для ответа `POST /uploads`; раньше ответ
  ссылался на `UploadedInfo`, которую используют ещё и payload'ы вложений `video`/`audio`/`file` (там `url` не нужен).
  `UploadedInfo` сохранена как есть (с `url`) — сознательное отклонение, `AGENTS.md` § 2.1. Схем стало 107, «нет у нас»
  41 → 40 (лишних по-прежнему 14).
- `SuccessResponse` — `required: [success]` (официальная `SimpleQueryResult`), закрывает все `POST/PUT/DELETE`,
  возвращающие `success`.
- Проставлен `required` в инлайновых 2xx-ответах: `messages` (`GET /messages`), `message` (`POST /messages`),
  `updates` (`GET /updates`), `subscriptions` (`GET /subscriptions`), `members` (`GET /chats/{chatId}/members` и
  `GET /chats/{chatId}/members/admins`).

Сознательно **не** тронуто: `marker` в теле `POST /chats/{chatId}/members/admins` — страница метода его документирует
(необязательный integer int64 Nullable), машинная схема (`ChatAdminsList`) нет. Зарегистрировано в `AGENTS.md` § 5 как
расхождение источников.

Синхронно обновлены:

- `MAX_API_REFERENCE.md`: `notification` в теле `POST /answers`; `success` — обязательное поле ответа; ответ
  `POST /uploads` — таблица с колонкой «Обязательное», `url` = **Да**, `token` nullable, схема `UploadEndpoint`; раздел
  `UploadedInfo` переименован в «payload вложений video, audio, file»; исправлена фраза «Как это работает».
- `DOCS_MAP.md` § 1: 106 → 107 схем, 41 → 40 отсутствующих, из таблицы убраны несуществующий
  `ShareAttachmentRequestPayload` (→ `VideoAttachmentDetails`) и опечатка `ModifyResults`, удалена строка
  `FailedUserDetails` (схема возвращена 2026-10-19); § 7.2 — новые цифры и упоминание `op_bodies_diff.py`.
- `AGENTS.md`: § 2 (107 схем), § 2.1 (строка `UploadedInfo`/`UploadEndpoint`), § 5 (расхождение по `marker`), § 7.1
  (компаратор тел, цифры 40/14, «настоящие расхождения»).
- `README.md`: «Последнее обновление» — 2026-10-20, 107 схем.

## Проверка

Прогон 2026-10-20 после всех правок (цифры — из прогона, не из памяти):

- `python3 -c "import yaml; yaml.safe_load(...)"` → `OK`;
- разрешение `$ref` → «Все 454 ссылок резолвятся»;
- дубли ключей YAML → «дублей ключей нет»;
- `openapi_spec_validator` → «OpenAPI 3.1.0 валидна»;
- `diff_official.py` → пути 18 = 18, операции 33 = 33, **официально 133 / у нас 107 схем, нет у нас 40, лишних 14**,
  битых ссылок нет;
- `types_diff.py` → nullability-расхождений 2 (`Message.body`, `admin_id` — оба зарегистрированы), enum-расхождений 0 (2
  строки — только порядок значений);
- `op_bodies_diff.py` → остались только зарегистрированные отклонения: `marker` в теле `POST .../members/admins` и
  `name` в ответах `GET /me` / `GET /chats/{chatId}/members/me`.

Выводы сохранены: `/tmp/opencode/diff_2026-10-20b.txt`, `/tmp/opencode/types_2026-10-20b.txt`,
`/tmp/opencode/bodies_2026-10-20.txt`.

## Нюансы

- Официальная схема не менялась (`1a4a502`, v0.0.33), клон и компараторы после сброса окружения пересозданы.
- `UploadedInfo` намеренно оставлена с `url`: это payload вложений, не ответ `POST /uploads`; разделение на два объекта
  повторяет официальную схему (`UploadedInfo` + `UploadEndpoint`) и снимает противоречие «`url` обязателен» из § 2.1.
- `op_bodies_diff.py` появился в этой сессии; при смене окружения его нужно пересоздать (как и остальные компараторы,
  `AGENTS.md` § 7.1). Запуск: `python3 /tmp/opencode/op_bodies_diff.py`.
- Коммита нет — только по явному запросу пользователя (`AGENTS.md` § 6.2).
