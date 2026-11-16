---
tags: [ openapi, alignment, refactor, codegen ]
date: 2026-11-16
status: в работе
---

# План: приведение `openapi.yaml` к официальной `schema.yaml` (v0.0.34)

## Цель

Сделать нашу спеку структурно и по именам совместимой с официальной машинной схемой
`https://github.com/max-messenger/api-schema` (v0.0.34, коммит `0016ff3`), сохранив **OpenAPI 3.1.0**
(версию стандарта не менять) и русские описания. Это уберёт расхождения по именам/структуре и обеспечит корректную
валидацию и генерацию клиентов/SDK, включая уже существующий `max-php-client`.

## Исходные данные

- Свежий клон официальной схемы: `/tmp/opencode/max-official/schema.yaml` (v0.0.34, коммит `0016ff3`).
- Полный diff: `/tmp/opencode/full_check_1116.txt` (результат `python3 tools/check_spec.py`).
- Официальная схема обновилась с v0.0.33 → v0.0.34: появилась схема `SimpleQueryResult` (поле `code`), 15 «простых»
  эндпоинтов теперь возвращают её как 2xx.

## Что меняем (по группам)

### 0. Версия + `SimpleQueryResult`/`code` (первый шаг)

- `info.x-official-schema.version` → `"0.0.34"`, `commit` → `"0016ff3"`, `verified` → `"2026-11-16"`.
- `SuccessResponse` → `SimpleQueryResult` + добавить nullable-поле `code`.
- `ErrorResponse` → `Error` (совпадение имени со схемой `Error`).

### 1. Алиасы и обёртки (механический, низкий риск)

- Алиасы: `UserId`, `ChatId`, `MessageId`, `bigint`, `Url`, `SubscriptionUrl`, `PhotoToken`.
- `MessageLinkType` (enum) — заменить инлайн-строки `type` у link-объектов.
- Обёртки: `MessageList`, `CommentMessageList`, `ChatList`, `ChatMembersList`, `ChatAdminsList`,
  `UpdateList`, `UserIdsList`, `GetSubscriptionsResult`, `GetPinnedMessageResult`,
  `ModifyMembersResult`, `SendMessageResult`, `SendCommentResult`.
- Тела запросов/ответов: `ActionRequestBody`, `BotCommandsInfo`, `BotCommandsPatch`, `ChatPatch`,
  `PinMessageBody`, `SubscriptionRequestBody`, `CallbackAnswer`.
- Поля `integer/int64` → `$ref` на `ChatId`/`UserId` (реестр § 4.1 AGENTS.md).

### 2. Переименования 1:1

- `ErrorResponse` → `Error`; `VideoInfo` → `VideoAttachmentDetails`;
  `SuccessResponse` → `SimpleQueryResult` (+`code`).

### 3. Вложения — перенос метаданных `payload` → верхний уровень

- `VideoAttachmentPayload`/`AudioAttachmentPayload` → общий `MediaAttachmentPayload`.
- Метаданные (`width`/`height`/`duration`/`thumbnail`, `filename`/`size`, `transcription`,
  `title`/`description`/`image_url`) — наружу из `payload` в подтип, как в официальной схеме.
- `AttachmentPayload` (базовый) + подтипы: `PhotoAttachmentPayload`, `MediaAttachmentPayload`,
  `FileAttachmentPayload`, `ContactAttachmentPayload`, `StickerAttachmentPayload`,
  `ShareAttachmentPayload`.

### 4. `Update` — полиморфизм

- Убрать `UpdateBase`, `UpdateType` (enum) и `oneOf`.
- `Update` = база (`update_type: string`, `timestamp`) + `discriminator` (propertyName `update_type`, mapping 19 типов);
  подтипы — `allOf: [$ref Update]`, без `enum`.

### 5. Кнопки/клавиатура

- Убрать `InlineKeyboardButton`, `InlineKeyboardButtonRow`, `ButtonType`.
- `Keyboard` (`buttons: array<array<Button>>`), `Button` (база, discriminator `type`) + 7 подтипов:
  `CallbackButton`, `LinkButton`, `MessageButton`, `RequestContactButton`,
  `RequestGeoLocationButton`, `OpenAppButton`, `ClipboardButton`.

### 6. Ответы `components/responses`

- Официальные: `SuccessResponse`, `InternalError`, `Unauthorized`, `Forbidden`, `NotFound`, `NotAllowed`.
- Убрать наши `BadRequest`, `TooManyRequests`, `ServiceUnavailable`, `MethodNotAllowed`.

### 7. Nullability + enum

- `Message.body` — убрать nullable (обязателен). `UserRemovedFromChatUpdate.admin_id` — убрать nullable.
- `Chat.type`, `Recipient.chat_type` — порядок enum `dialog, chat, channel`.
- `SenderAction` — добавить `mark_seen` (6-е значение).

### 8. Хвосты (снять зарегистрированные отклонения)

- `User.name` — убрать из 4 схем; `UploadedInfo.url` — убрать; `CommentMessage` в событиях комментариев → `Message`;
  `marker` в теле `POST /chats/{chatId}/members/admins` — убрать.
- Синхронизировать `REGISTERED` в `tools/check_spec.py` и разделы § 2.1/§ 5/§ 4.1 в `AGENTS.md`,
  `DOCS_MAP.md`, `README.md`.

## Порядок выполнения (шаги)

1. **Шаг 0** — версия + `SimpleQueryResult`/`Error` (группа 0, 2 частично).
2. **Шаг 1** — алиасы + обёртки + тела (группа 1).
3. **Шаг 2** — вложения (группа 3).
4. **Шаг 3** — `Update` (группа 4).
5. **Шаг 4** — кнопки (группа 5).
6. **Шаг 5** — ответы + nullability + enum + хвосты (группы 6–8).

После каждого шага: `python3 tools/check_spec.py --official /tmp/opencode/max-official/schema.yaml`, сверка `$ref`,
YAML-дубли, строгая валидация 3.1.0. Синхронизировать `MAX_API_REFERENCE.md` и
`REGISTERED`/`AGENTS.md` по мере закрытия отклонений.

## Нюансы / риски

- Nullability в 3.1 записывается только как `type: [x, "null"]` или `anyOf: [{$ref}, {type: "null"}]`
  (ключевое слово `nullable` не существует — AGENTS.md § 7.1).
- Официальная схема — OpenAPI 3.0 с `nullable: true`; переводим механически в 3.1-формы.
- Официальные описания местами короче наших; русские описания сохраняем, имена полей/схем — точь-в-точь.
- Смена `Update`/кнопок/вложений ломает публичные имена `max-php-client` — регенерация SDK и правка его кода — отдельный
  этап, после выравнивания спеки.
- Не удалять операцию `POST /chats/{chatId}/members` (живой метод, § 5 AGENTS.md).

## Статус

- [x] Шаг 0 — версия + `SimpleQueryResult`/`Error`
- [x] Шаг 1 — алиасы + обёртки + тела
- [x] Шаг 2 — вложения
- [x] Шаг 3 — `Update`
- [x] Шаг 4 — кнопки
- [x] Шаг 5 — ответы + nullability + enum + хвосты
- [x] Синхронизация `REGISTERED` (tools/check_spec.py) и README
- [x] Синхронизация `AGENTS.md` § 2.1/§ 4.1/§ 5/§ 7.1, `DOCS_MAP.md`, `MAX_API_REFERENCE.md`, `QUALITY.md`

## Итог реализации (2026-11-16)

`python3 tools/check_spec.py` → exit 0, «зарегистрированных отклонений: 0, новых расхождений нет». Имена схем 133 = 133,
поля/`required` совпадают, nullability/enum совпадают, strict 3.1.0 валидна. ID-поля конвертированы в `$ref`-алиасы
(`ChatId`/`UserId`/`MessageId`/`MessageLinkType`),
`operationId` выровнены под официальные (17 переименований). Остался «шум» types_diff (36 строк, не расхождения):
`null_form` (31 — 3.1 `anyOf` ↔ 3.0 `nullable`, неизбежно),
`format_uri` (4 — у нас `format: uri`), `alias` (1 — `UserIdsList.user_ids`: в официальной схеме нет `type: array`),
порядок enum. Всё это не расхождения и на типы SDK не влияет.

## Закрытый вопрос (пункт 2)

ID-поля (`chat_id`, `user_id`, `mid`, …) конвертированы из `integer/int64`/`string` в `$ref`-алиасы
`ChatId`/`UserId`/`MessageId`/`MessageLinkType` — 2026-11-16 (41 поле: 24 не-nullable int, 6 nullable int, 7 string ID,
1 nullable string ID, 3 link `type`). Для рукописного `max-php-client` это ноль эффекта (типы клиента вручную объявлены
и не читаются из спеки).
