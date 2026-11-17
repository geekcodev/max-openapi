---
tags: [ openapi, alignment, refactor, codegen, schema, validation ]
date: 2026-11-16
---

# Приведение спеки к официальной `schema.yaml` v0.0.34

## Проблема

Спека была собрана по текстовой доке до выхода официальной машинной схемы и накопила сознательные отклонения (§ 2.1
`AGENTS.md`): свои имена схем (`InlineKeyboardButton`, `VideoInfo`, `SuccessResponse`, `UpdateBase`, …), свой
полиморфизм (`oneOf`+`enum`), метаданные вложений в `payload`, инлайн ID-поля. Задача — привести имена и структуру к
официальной `max-messenger/api-schema` (v0.0.34, коммит `0016ff3`, обновилась с v0.0.33), сохранив **OpenAPI 3.1.0** и
русские описания, чтобы проходила валидация и генерация клиентов/SDK (в т.ч. `max-php-client`).

## Решение

Полная реструктуризация `openapi.yaml` (без правки версии стандарта — осталась 3.1.0):

- **Версия**: `info.x-official-schema` → `0.0.34` / `0016ff3` / `2026-11-16`.
- **Схемы (имена)**: 107 → 133, все совпадают с официальными. Добавлены алиасы (`UserId`, `ChatId`,
  `MessageId`, `bigint`, `Url`, `SubscriptionUrl`, `PhotoToken`, `MessageLinkType`), обёртки (`MessageList`, `ChatList`,
  `ChatMembersList`, `ChatAdminsList`, `UpdateList`, `UserIdsList`, `GetSubscriptionsResult`, `GetPinnedMessageResult`,
  `ModifyMembersResult`, `SendMessageResult`), тела (`ActionRequestBody`, `BotCommandsInfo`, `BotCommandsPatch`,
  `ChatPatch`, `PinMessageBody`, `SubscriptionRequestBody`, `CallbackAnswer`), кнопки (`Button` + 7 подтипов +
  `Keyboard` + `InlineKeyboardAttachmentRequestPayload`), базовые payload вложений (`AttachmentPayload`,
  `MediaAttachmentPayload`), `SimpleQueryResult` (+nullable `code`), `Error`.
- **Переименования**: `VideoInfo`→`VideoAttachmentDetails`, `SuccessResponse`→`SimpleQueryResult`,
  `ErrorResponse`→`Error`, `VideoAttachmentPayload`/`AudioAttachmentPayload`→`MediaAttachmentPayload`,
  `InlineKeyboardAttachmentPayload`→`Keyboard`.
- **Удалены** свои схемы: `UpdateBase`, `UpdateType`, `AttachmentBase`, `AttachmentRequestBase`,
  `AttachmentType`, `ButtonType`, `InlineKeyboardButton`, `InlineKeyboardButtonRow`.
- **Структура**: `Update` = база (`update_type: string`, `timestamp`) + `discriminator` (без `oneOf`/`enum`); то же для
  `Attachment`/`AttachmentRequest`; кнопки — `Button` с `discriminator` по `type` и 7 подтипов через `allOf`; метаданные
  вложений (`width`/`height`/`duration`/`thumbnail`/`filename`/`size`/
  `transcription`/`title`/`description`/`image_url`) перенесены из `payload` на верхний уровень подтипов.
- **Хвосты**: `User.name` и `UploadedInfo.url` удалены; события комментариев ссылаются на `Message`;
  `Message.body` и `UserRemovedFromChatUpdate.admin_id` больше не nullable; `SenderAction` + `mark_seen`; параметры
  `chatId`/`messageId` инлайнены; `marker` убран из тела `POST .../members/admins`;
  `components/responses` переименованы под официальные (`SuccessResponse`/`InternalError`/`Unauthorized`/
  `Forbidden`/`NotFound`/`NotAllowed`), из операций убраны ссылки на 400/429/503.

## Проверка

`python3 tools/check_spec.py --official /tmp/opencode/max-official/schema.yaml` (с `OAS_PYTHON` venv
`openapi-spec-validator`) → **код возврата 0**:

- YAML OK, дублей ключей нет, `$ref` 350 (схемы/ответы), битых нет;
- **OpenAPI 3.1.0 валидна** (строгая проверка `openapi-spec-validator`);
- версия `0.0.34`/`0016ff3` совпадает;
- пути 18 = 18, операции 33 = 33, **схемы 133 = 133** (нет/лишних нет);
- поля/`required` совпадают, nullability 0, enum 0, настоящих типовых расхождений 0;
- тела запросов/2xx-ответов совпадают;
- **зарегистрированных отклонений 0, новых 0**.

`REGISTERED` в `tools/check_spec.py` опустошён (отклонений больше нет).

## Нюансы / осталось

- ID-поля конвертированы в `$ref`-алиасы (`ChatId`/`UserId`/`MessageId`/`MessageLinkType`) — 41 поле (пункт 2).
- `operationId` выровнены под официальные (17 переименований: `getMe`→`getMyInfo`, `addChatAdmin`→`postAdmins`,
  `sendAnswer`→`answerOnCallback`, `uploadMedia`→`getUploadUrl`, `getVideoInfo`→`getVideoAttachmentDetails` и др.).
- «Шум» `types_diff` (36 строк, не расхождения): `null_form` (31 — 3.1 `anyOf` vs 3.0 `nullable`, неизбежно при 3.1),
  `format_uri` (4 — `format: uri`), `alias` (1 — `UserIdsList.user_ids`: в официальной схеме нет `type: array`), порядок
  enum. На типы SDK не влияет.
- Синхронизированы `AGENTS.md` § 2.1/§ 4.1/§ 5/§ 7.1, `DOCS_MAP.md`, `MAX_API_REFERENCE.md`, `QUALITY.md`, `README.md`.
- Повторная сверка `MAX_API_REFERENCE.md` (по запросу) нашла и исправила остаточные неактуализированные места:
  `message` в событиях комментариев (→ `Message`), `admin_id` nullable, `Message.body` nullable (2 места + примечание),
  лимиты кнопок (текст 2048→128, payload 8КБ→1024/512), `SenderAction` без `mark_seen`, `marker` в теле
  `POST .../members/admins`, порядок enum `ChatType` (2 места), примечание про `ShareAttachmentRequestPayload`, поле
  `User.name` (3 таблицы + примечания).
- Коммита нет (по правилам — только по явному запросу).

## Дополнение (проверка остальных файлов + коды ответов + README)

- Повторная сверка остальных `.md`-файлов нашла и исправила: `AGENTS.md` §2 (107→133 схемы, 473→391 `$ref`), §7.1
  (пример `x-official-schema` 0.0.33→0.0.34), §4 (лимиты кнопок), §5.1 п.1 (8 КБ → закрыто), п.8 (MarkupElement —
  закрыто, исправлен ключ `underlined`→`underline`); `README.md` §2 (107→133 схемы); `MAX_API_REFERENCE.md` (шапка
  «Последнее обновление» и 2 примечания v0.0.33→v0.0.34).
- **Коды ответов об ошибках** выровнены под официальные: убраны `BadRequest`(400)/`TooManyRequests`(429)/
  `ServiceUnavailable`(503), добавлены `Forbidden`(403)/`InternalError`(500) по каждому эндпоинту — разница кодов по 33
  операциям стала 0 (это расхождение компараторы не видят, оно найдено отдельной проверкой).
- В `README.md` добавлен раздел «Совместимость с официальной схемой» (ссылка на `max-messenger/api-schema`, таблица
  намеренных отличий и косметических) и обновлена шапка + строка «Коды ответов».
