# DOCS_MAP — карта официальной документации MAX API

Навигация по `dev.max.ru` + регламент отслеживания изменений. Задача файла: за одну сессию быстро понять, **где искать
информацию** и **как обнаружить, что метод изменился**.

Связанные файлы: `openapi.yaml` (спека), `MAX_API_REFERENCE.md` (справочник), `AGENTS.md` (правила, ключевые факты,
сознательные отклонения, реестр полей). (расхождения). Правило источника истины — `AGENTS.md` §3: **только официальная
дока, факт = URL + дата проверки**.

> Состояние карты: **2026-09-27**. Официальная спека `api-schema` — версия `0.0.33`, коммит 2026-09-18.

---

## 1. Быстрый вход: куда смотреть в первую очередь

| Задача                                  | URL                                                           | Комментарий                                                             |
|-----------------------------------------|---------------------------------------------------------------|-------------------------------------------------------------------------|
| **Проверить, что изменилось в API**     | `https://dev.max.ru/docs-api/changelog-api`                   | **Главный источник для релизов.** Три «журнала изменений» на платформе  |
| Проверить изменения платформы/док       | `https://dev.max.ru/docs/changelog-platform`                  | Правки разделов `/docs`, не методов                                     |
| Точка входа «что вообще есть»           | `https://dev.max.ru/docs-api`                                 | Обзор, авторизация, коды ответов, список всех методов и объектов        |
| **Сверить машинно** спеку с официальной | `https://github.com/max-messenger/api-schema` → `schema.yaml` | Единственный источник правды по типам/полям, diff вместо ручного чтения |

**Официальный репозиторий спецификации** — ключевая находка (сентябрь 2026). Локальный `openapi.yaml` собран вручную и
намеренно отстаёт от официальной схемы по объёму: официальная — OpenAPI **3.0.0**, 18 путей, 133 схемы; наша — 3.1.0, 18
путей, 32 метода, 105 схем. **Пути совпадают с официальной схемой** (18 = 18): удалённый в июне 2026 `GET /chats`
убран из нашей спеки 2026-09-27 (см. § 6, пп. 7 и 9). По операциям на один меньше — см. примечание в конце § 4.

**Сверка схем после рефакторинга `Update` и вложений (2026-09-27).** Официальных схем нет у нас — 42, лишних у нас — 14.
Обе цифры объясняются осознанно:

| У нас лишние (14)                                                                                               | Причина                                                                                                |
|-----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `UpdateBase`, `AttachmentBase`, `AttachmentRequestBase`                                                         | базы для `allOf` — официальные подтипы не выносят общую часть в отдельную схему                        |
| `UpdateType`, `AttachmentType`                                                                                  | наши `enum`-перечисления (в официальной схеме значения перечислены прямо в полях)                      |
| `VideoInfo`, `InlineKeyboardButton`, `InlineKeyboardButtonRow`, `InlineKeyboardAttachmentPayload`, `ButtonType` | клавиатура: официальная схема описывает кнопки как `oneOf` без именованных подсхем                     |
| `SuccessResponse`, `ErrorResponse`                                                                              | обёртки ответов                                                                                        |
| `VideoAttachmentPayload`, `AudioAttachmentPayload`                                                              | официальные подтипы кладут `url`/`token` на верхний уровень, мы — в `payload` (`AGENTS.md` § 2.1 п. 7) |

Отсутствующие у нас 42 схемы — не упущения, а сознательные решения:

| Группа                         | Схемы                                                                                                                                                                                                                                                                                                                                                                                                   | Почему нет у нас                                                                                                                                                           |
|--------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Псевдонимы скаляров            | `ChatId`, `UserId`, `MessageId`, `Url`, `PhotoToken`, `bigint`, `UserIdsList`, `MessageLinkType`                                                                                                                                                                                                                                                                                                        | официальная схема выносит типы в именованные псевдонимы; мы пишем типы прямо в полях                                                                                       |
| Клавиатура                     | `Button`, `CallbackButton`, `LinkButton`, `MessageButton`, `RequestContactButton`, `RequestGeoLocationButton`, `OpenAppButton`, `ClipboardButton`, `Keyboard`                                                                                                                                                                                                                                           | официальная схема — `oneOf` из 7 кнопок без дискриминатора; у нас одна `InlineKeyboardButton` с `enum` `ButtonType` (это делает тип проверяемым)                           |
| Обёртки запросов и результатов | `ActionRequestBody`, `BotCommandsInfo`, `BotCommandsPatch`, `ChatPatch`, `SubscriptionRequestBody`, `PinMessageBody`, `SimpleQueryResult`, `SendMessageResult`, `MessageList`, `UpdateList`, `ChatList`, `ChatAdminsList`, `ChatMembersList`, `GetSubscriptionsResult`, `GetPinnedMessageResult`, `ModifyResults`/`ModifyMembersResult`, `Error`, `CallbackAnswer`, `UploadEndpoint`, `SubscriptionUrl` | официальная схема именует каждую обёртку; у нас тело/ответ задаются `$ref` прямо на схему данных, без промежуточного имени                                                 |
| Заглушки официальной схемы     | `AttachmentPayload`, `MediaAttachmentPayload`, `InlineKeyboardAttachmentRequestPayload`, `ShareAttachmentRequestPayload`                                                                                                                                                                                                                                                                                | первые три — общие/пустые placeholders (`MediaAttachmentPayload` и `ShareAttachmentRequestPayload` вообще без полей); у нас payload привязан к конкретному `type` вложения |
| Снято вместе с методом         | `FailedUserDetails`                                                                                                                                                                                                                                                                                                                                                                                     | удалён вместе с `POST /chats/{chatId}/members` (§ 5.2 `AGENTS.md`)                                                                                                         |

Структурные решения — `AGENTS.md` § 2.1, известные артефакты скрипта — `AGENTS.md` § 7.1.

```bash
# разовая сверка (клонировать один раз в /tmp)
git clone --depth 1 https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official
# в официальной схеме смотреть: paths, components.schemas, components.responses
```

---

## 2. Разделы `/docs-api`

| Раздел                           | URL-шаблон                                                 | Что внутри                                                                     |
|----------------------------------|------------------------------------------------------------|--------------------------------------------------------------------------------|
| Общее описание                   | `/docs-api`                                                | Авторизация, семантика HTTP-методов, коды ответов, ссылка на OpenAPI-спеку     |
| Сценарии: уведомления о событиях | `/docs-api/use-cases/event-notifications`                  | Вебхуки, ретраи, заголовок `X-Max-Bot-Api-Secret`, таймауты                    |
| Сценарии: получение `chat_id`    | `/docs-api/use-cases/getting-chat-id`                      | Как бот узнаёт `chat_id` (важно: `GET /chats` **удалён**, собирать из событий) |
| Сценарии: команды чат-бота       | `/docs-api/use-cases/chatbot-commands`                     | Соответствует `PATCH /me/commands`                                             |
| Отправка: форматирование текста  | `/docs-api/use-cases/sending-messages/text-formatting`     | Markdown и HTML-подмножество                                                   |
| Отправка: типы вложений          | `/docs-api/use-cases/sending-messages/attachment-types`    | `Attachment`-payload'ы по типам                                                |
| Отправка: клавиатура             | `/docs-api/use-cases/sending-messages/keyboard`            | 7 типов кнопок, лимиты 210/30/7                                                |
| Отправка: медиафайлы             | `/docs-api/use-cases/sending-messages/media`               | **Лимиты video/audio/image/file**, resumable, multipart                        |
| Отправка: стикеры и контакты     | `/docs-api/use-cases/sending-messages/another-attachments` | `StickerAttachment`, `ContactAttachment`                                       |
| Модерация комментариев           | `/docs-api/use-cases/comment-moderation`                   | Права `read_all_messages`/`write_all_messages`, сценарии комментариев          |
| История изменений API            | `/docs-api/changelog-api`                                  | Журнал релизов по группам: Bots / Chats / Comments / Uploads / Messages        |
| Методы                           | `/docs-api/methods/{VERB}/{path-шаблон}`                   | 32 метода в 7 группах, см. §4                                                  |
| Объекты                          | `/docs-api/objects/{Object}`                               | 11 страниц объектов, см. §5                                                    |

**Правило формирования URL метода.** Фигурные скобки пути заменяются на `-имя-`:
`/chats/{chatId}` → `/docs-api/methods/GET/chats/-chatId-`. Вложенный путь:
`/messages/{messageId}/comments/{commentId}` → `/docs-api/methods/GET/messages/-messageId-/comments/-commentId-`.

---

## 3. Разделы `/docs` (платформа, не Bot API)

| Раздел                                           | URL                                                                                                |
|--------------------------------------------------|----------------------------------------------------------------------------------------------------|
| О платформе                                      | `/docs`                                                                                            |
| Подключение: профиль организации/ИП/самозанятого | `/docs/maxbusiness/connection`                                                                     |
| Подключение: выбор сервисов                      | `/docs/maxbusiness/selectionservices`                                                              |
| Чат-боты: создание                               | `/docs/chatbots/bots-create/create`                                                                |
| Чат-боты: управление                             | `/docs/chatbots/bots-create/manage`                                                                |
| Чат-боты: конструктор без кода                   | `/docs/chatbots/bots-nocode`                                                                       |
| Чат-боты: разработка с кодом (подготовка)        | `/docs/chatbots/bots-coding/prepare`                                                               |
| Чат-боты: библиотека JavaScript                  | `/docs/chatbots/bots-coding/js` → [GitHub](https://github.com/max-messenger/max-bot-api-client-ts) |
| Чат-боты: библиотека Golang                      | `/docs/chatbots/bots-coding/go` → [GitHub](https://github.com/max-messenger/max-bot-api-client-go) |
| Чат-боты: примеры                                | `/docs/chatbots/bots-coding/examples`                                                              |
| Мини-приложения: общее описание                  | `/docs/webapps/introduction`                                                                       |
| Мини-приложения: MAX Bridge                      | `/docs/webapps/bridge`                                                                             |
| Мини-приложения: валидация данных                | `/docs/webapps/validation` — WebAppData, `auth_date`, hash `request_contact`                       |
| Каналы: создание                                 | `/docs/channels/create`                                                                            |
| Каналы: управление                               | `/docs/channels/manage`                                                                            |
| Цифровой ID                                      | `/docs/digital-id`                                                                                 |
| Интеграция с партнёрами                          | `/docs/partners-integration`                                                                       |
| **Open Client API**                              | `/docs/open-api` — **новый раздел, в `AGENTS.md` не зафиксирован**                                 |
| Правила площадки                                 | `/docs/legal/rules`, `/docs/legal/requirements`, `/docs/legal/agreement`, `/docs/legal/privacy`    |
| История изменений платформы                      | `/docs/changelog-platform`                                                                         |
| MAX UI (дизайн-система)                          | `/ui`                                                                                              |
| Справка                                          | `/help`                                                                                            |
| Журнал изменений (переключатель)                 | `/changelog-docs` — ведёт на два журнала выше                                                      |

---

## 4. Карта методов (32 метода в 7 группах)

`✓` = есть в `openapi.yaml`, `—` = отсутствует.

### bots (2)

| Метод | Путь           | Doc-URL                               | В спеке        |
|-------|----------------|---------------------------------------|----------------|
| GET   | `/me`          | `/docs-api/methods/GET/me`            | ✓             |
| PATCH | `/me/commands` | `/docs-api/methods/PATCH/me/commands` | ✓ (июль 2026) |

### chats (13)

| Метод  | Путь                                      | Doc-URL                                                           | В спеке                 |
|--------|-------------------------------------------|-------------------------------------------------------------------|-------------------------|
| GET    | `/chats/{chatId}`                         | `/docs-api/methods/GET/chats/-chatId-`                            | ✓                      |
| PATCH  | `/chats/{chatId}`                         | `/docs-api/methods/PATCH/chats/-chatId-`                          | ✓ (есть `description`) |
| POST   | `/chats/{chatId}/actions`                 | `/docs-api/methods/POST/chats/-chatId-/actions`                   | ✓                      |
| GET    | `/chats/{chatId}/pin`                     | `/docs-api/methods/GET/chats/-chatId-/pin`                        | ✓                      |
| PUT    | `/chats/{chatId}/pin`                     | `/docs-api/methods/PUT/chats/-chatId-/pin`                        | ✓                      |
| DELETE | `/chats/{chatId}/pin`                     | `/docs-api/methods/DELETE/chats/-chatId-/pin`                     | ✓                      |
| GET    | `/chats/{chatId}/members/me`              | `/docs-api/methods/GET/chats/-chatId-/members/me`                 | ✓                      |
| DELETE | `/chats/{chatId}/members/me`              | `/docs-api/methods/DELETE/chats/-chatId-/members/me`              | ✓                      |
| GET    | `/chats/{chatId}/members/admins`          | `/docs-api/methods/GET/chats/-chatId-/members/admins`             | ✓                      |
| POST   | `/chats/{chatId}/members/admins`          | `/docs-api/methods/POST/chats/-chatId-/members/admins`            | ✓                      |
| DELETE | `/chats/{chatId}/members/admins/{userId}` | `/docs-api/methods/DELETE/chats/-chatId-/members/admins/-userId-` | ✓                      |
| GET    | `/chats/{chatId}/members`                 | `/docs-api/methods/GET/chats/-chatId-/members`                    | ✓                      |
| DELETE | `/chats/{chatId}/members`                 | `/docs-api/methods/DELETE/chats/-chatId-/members`                 | ✓                      |

### subscriptions (3) + Long Polling (1)

| Метод  | Путь             | Doc-URL                                  | В спеке |
|--------|------------------|------------------------------------------|---------|
| GET    | `/subscriptions` | `/docs-api/methods/GET/subscriptions`    | ✓      |
| POST   | `/subscriptions` | `/docs-api/methods/POST/subscriptions`   | ✓      |
| DELETE | `/subscriptions` | `/docs-api/methods/DELETE/subscriptions` | ✓      |
| GET    | `/updates`       | `/docs-api/methods/GET/updates`          | ✓      |

### upload (1)

| Метод | Путь       | Doc-URL                          | В спеке |
|-------|------------|----------------------------------|---------|
| POST  | `/uploads` | `/docs-api/methods/POST/uploads` | ✓      |

### messages (7)

| Метод  | Путь                    | Doc-URL                                      | В спеке |
|--------|-------------------------|----------------------------------------------|---------|
| GET    | `/messages`             | `/docs-api/methods/GET/messages`             | ✓      |
| POST   | `/messages`             | `/docs-api/methods/POST/messages`            | ✓      |
| PUT    | `/messages`             | `/docs-api/methods/PUT/messages`             | ✓      |
| DELETE | `/messages`             | `/docs-api/methods/DELETE/messages`          | ✓      |
| GET    | `/messages/{messageId}` | `/docs-api/methods/GET/messages/-messageId-` | ✓      |
| GET    | `/videos/{videoToken}`  | `/docs-api/methods/GET/videos/-videoToken-`  | ✓      |
| POST   | `/answers`              | `/docs-api/methods/POST/answers`             | ✓      |

### comments (5) — **добавлено в спеке 2026-09-27**

| Метод  | Путь                                         | Doc-URL                                                           | В спеке |
|--------|----------------------------------------------|-------------------------------------------------------------------|---------|
| GET    | `/messages/{messageId}/comments`             | `/docs-api/methods/GET/messages/-messageId-/comments`             | ✓      |
| POST   | `/messages/{messageId}/comments`             | `/docs-api/methods/POST/messages/-messageId-/comments`            | ✓      |
| PUT    | `/messages/{messageId}/comments`             | `/docs-api/methods/PUT/messages/-messageId-/comments`             | ✓      |
| DELETE | `/messages/{messageId}/comments`             | `/docs-api/methods/DELETE/messages/-messageId-/comments`          | ✓      |
| GET    | `/messages/{messageId}/comments/{commentId}` | `/docs-api/methods/GET/messages/-messageId-/comments/-commentId-` | ✓      |

> `PUT` и `DELETE` передают `comment_id` query-параметром. Комментарий создаётся **только в канале**:
> `recipient.chat_type: channel` + `recipient.post_id`. События `comment_created` / `comment_edited` /
> `comment_removed` приходят боту только с правом `read_all_messages`.

> Пути совпадают: **18 официально = 18 у нас** (после удаления `GET /chats` 2026-09-27). Методов на один меньше:
> **32 у нас против 33 официально** — из `POST /chats/{chatId}/members` удалена только операция `post` (сам путь
> остался из-за `get`/`delete`), потому что метод объявлен удаляемым 30.09.2026, а официальная `schema.yaml` на
> 2026-09-27 ещё держит и путь, и операцию. После 30.09.2026 ожидаемое расхождение исчезнет само.

---

## 5. Карта объектов (11 страниц в доках)

| Объект           | URL                                | В спеке                            |
|------------------|------------------------------------|------------------------------------|
| `User`           | `/docs-api/objects/User`           | ✓                                 |
| `UserWithPhoto`  | `/docs-api/objects/UserWithPhoto`  | ✓                                 |
| `BotInfo`        | `/docs-api/objects/BotInfo`        | ✓                                 |
| `ChatMember`     | `/docs-api/objects/ChatMember`     | ✓ (enum 14 значений с deprecated) |
| `Chat`           | `/docs-api/objects/Chat`           | ✓                                 |
| `Message`        | `/docs-api/objects/Message`        | ✓                                 |
| `CommentMessage` | `/docs-api/objects/CommentMessage` | ✓                                 |
| `NewMessageBody` | `/docs-api/objects/NewMessageBody` | ✓                                 |
| `NewCommentBody` | `/docs-api/objects/NewCommentBody` | ✓                                 |
| `Update`         | `/docs-api/objects/Update`         | ✓                                 |

**Страниц объекта в доках нет**, но в официальной схеме определены (использовать как источник по полям):
`ActionRequestBody`, `Callback`, `CallbackAnswer`, `CommentLinkedMessage`, `Error`, `MessageBody`, `MessageStat`,
`Recipient`, `Subscription`, `UploadedInfo`, `UpdateList`, `MessageList`, `CommentMessageList`, `ChatList`,
`ChatMembersList`, `ChatAdminsList`, `GetSubscriptionsResult`, `SendMessageResult`, `SendCommentResult`, `Keyboard`,
`Button` и 7 подтипов кнопок, `Attachment` и ~20 payload-схем вложений, `MarkupElement` и 10 подтипов разметки, 11
`*Update`-схем (по одной на тип события).

**Разрешённые значения `Recipient.chat_type`** (закрывает `AGENTS.md` §5.1 п. 4): `dialog`, `chat`, `channel`.

---

## 6. Известные расхождения на 2026-09-27 (сводка для сверки)

Проход 2026-09-27 закрыл пп. 1–8. Открытые пункты перенесены в `AGENTS.md` § 5.1 и § 2.1.

| #  | Расхождение                                                                                                                                                                                 | Источник                                                                       | Статус                                                          |
|----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------|
| 1  | ~~**5 методов comments отсутствуют** в `openapi.yaml`~~                                                                                                                                     | changelog-api, август 2026                                                     | **закрыто 2026-09-27**                                          |
| 2  | ~~**3 события комментариев отсутствуют** в `Update`: `comment_created`, `comment_removed`, `comment_edited`~~                                                                               | changelog-api, август 2026                                                     | **закрыто 2026-09-27**                                          |
| 3  | ~~`LinkedMessage`: в спеке `sender: integer/int64` + поля `chat`, `mid`; официально `sender` → **объект `User`**, поля `chat_id` + `message` (`MessageBody`), `required: [type, message]`~~ | `api-schema`                                                                   | **закрыто 2026-09-27**, `AGENTS.md` § 5.1 п. 5                  |
| 4  | ~~`NewMessageLink`: в спеке enum `reply`/`forward`; официально enum **`forward`/`reply`** (порядок) и `required: [type, mid]`~~                                                             | `api-schema`                                                                   | **закрыто 2026-09-27**, `AGENTS.md` § 5.1 пп. 3, 4, 6           |
| 5  | ~~`LinkedMessage.type`: в спеке `forwarded`/`reply`; официально `forward`/`reply`~~                                                                                                         | `api-schema`                                                                   | **закрыто 2026-09-27**                                          |
| 6  | ~~`PATCH /chats/{chatId}` — нет поля `description` (официально: до 16000 символов, пустая строка снимает)~~                                                                                 | changelog-api, август 2026                                                     | **закрыто 2026-09-27**                                          |
| 7  | ~~`POST /chats/{chatId}/members` — ограничение с 09.09.2026, **удаление 30.09.2026**~~                                                                                                      | **только** страница метода (changelog упоминает лишь ограничение с 09.09.2026) | **закрыто 2026-09-27** — метод удалён из спеки за 3 дня до даты |
| 8  | `disable_link_preview` — добавлен в `POST /answers`; в официальной схеме также у `POST /messages`                                                                                           | `api-schema`                                                                   | **закрыто 2026-09-27**                                          |
| 9  | ~~`GET /chats` — в официальной схеме путь **удалён**, мы держали его как `deprecated`~~                                                                                                     | changelog-api, июнь 2026                                                       | **закрыто 2026-09-27** — путь удалён из спеки и справочника     |
| 10 | Ответы используют коды 403/405/500, которых нет в списке кодов на `/docs-api`                                                                                                               | `api-schema`                                                                   | баг док, в AGENTS.md §5                                         |
| 11 | Раздел `/docs/open-api` не зафиксирован в `AGENTS.md` §3                                                                                                                                    | `/docs`                                                                        | **закрыто 2026-09-27**                                          |
| 12 | Официальная схема — OpenAPI **3.0.0**, наша — 3.1.0; 133 схемы против 105                                                                                                                   | `api-schema`                                                                   | сознательное решение, `AGENTS.md` § 2.1 и § 5.1                 |
| 13 | ~~Плоский `Update` вместо `oneOf` + `discriminator`~~                                                                                                                                       | `api-schema`                                                                   | **закрыто 2026-09-27** — 19 подтипов + `UpdateBase`             |
| 14 | ~~`Attachment` без подтипов; `location` прятал координаты в `payload`~~                                                                                                                     | `api-schema`                                                                   | **закрыто 2026-09-27** — 9+9 подтипов, координаты наверху       |

**Открытые расхождения** после прохода 2026-09-27 — в `AGENTS.md` § 5.1 и § 2.1. Остались только сознательные решения:
именованные базы `UpdateBase`/`AttachmentBase`/`AttachmentRequestBase`, размещение части метаданных вложений внутри
`payload`, `ShareAttachmentPayload` вместо пустого `ShareAttachmentRequestPayload`, `url` в `UploadedInfo`, версия
OpenAPI 3.1.0 (с 2026-09-27 nullability выражена 3.1-легально: `type: [x, "null"]` и `anyOf` с `- type: "null"` вместо
ключевого слова
`nullable`, которого в 3.1 нет; официальная схема использует `nullable` 105 раз как 3.0.x-расширение — при сверке форм
это ожидаемое расхождение, не ошибка)
неподтверждённых полей **не осталось** (сверка с текстовой докой 2026-09-27): `MessageBody.caption`/`.format`
и `PhotoAttachmentPayload.width`/`height` удалены как неподтверждённые, `User.name` (в 4 схемах) и
`UploadedInfo.url` подтверждены страницами доков. Покрытие полей всех 6 подтипов вложений полное (проверено 2026-09-27
симметричным компаратором с разворачиванием `allOf`): добавлены
`StickerAttachmentPayload.code`/`url`/`width`/`height`, `FileAttachmentPayload.filename`/`size`
(вместо неподтверждённого `file_size`), `VideoAttachmentPayload.width`/`height`/`thumbnail`,
`AudioAttachmentPayload.transcription`, `ShareAttachmentPayload.title`/`description`/`image_url`, схема
`VideoThumbnail`, а также `required` у `VideoAttachmentPayload`, `AudioAttachmentPayload`,
`InlineKeyboardAttachmentPayload` и `ChatMember`. Расхождения по полям (`VideoUrls`,
`PhotoAttachmentPayload`, `ContactAttachmentPayload`) закрыты. `FailedUserDetails` исправлена была и затем удалена
вместе с операцией `POST /chats/{chatId}/members`.

---

## 7. Регламент: как ловить релизы

### 7.1 Быстрая проверка (раз в 1–2 недели)

1. Открыть `/docs-api/changelog-api` — это **единственная** точка правок методов. Сравнить верхний месяц с
   `AGENTS.md` §4 / `README.md` «Последнее обновление».
2. Сверить с официальной `schema.yaml`: `version:` в шапке и состав `paths` / `components.schemas`.
3. Если изменилось — править **оба** файла: `openapi.yaml` и `MAX_API_REFERENCE.md` (`AGENTS.md` §6 п. 2).
4. Запустить валидацию из `AGENTS.md` §7 и обновить дату в `README.md`.

### 7.2 Машинная сверка (когда расхождений много)

```bash
git clone --depth 1 https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official
python3 - <<'PY'
import yaml
off = yaml.safe_load(open('/tmp/opencode/max-official/schema.yaml'))
our = yaml.safe_load(open('openapi.yaml'))
o, u = set(off['paths']), set(our['paths'])
print('нет в нашей спеке:', sorted(o - u))
print('лишние у нас:     ', sorted(u - o))
os_, us_ = set(off['components']['schemas']), set(our['components']['schemas'])
print('схем нет у нас:', len(os_ - us_), '| лишних у нас:', sorted(us_ - os_))
PY
```

> Ожидаемый результат на 2026-09-27 (после рефакторинга `Update` и вложений): **пути — пусто в обе стороны**;
> операций — официально на 1 больше (`POST /chats/{chatId}/members`, удаляется 30.09.2026);
> **схем нет у нас 42, лишних у нас 14**. Обе цифры разобраны по группам в § 1; решения — `AGENTS.md` § 2.1,
> артефакты скрипта — `AGENTS.md` § 7.1.

### 7.3 Проверка конкретного метода на изменение

1. Открыть `/docs-api/changelog-api` и найти группу метода (Bots / Chats / Comments / Uploads / Messages).
2. Если метод в списке — открыть его Doc-URL из § 4 и сверить параметры/тело с нашей спекой.
3. Отдельно проверить `schema.yaml` по имени схемы ответа — там сразу видны добавленные поля.
4. Зафиксировать результат по регламенту `AGENTS.md` § 7.1: подтверждение — в § 4 / § 4.1, сознательное отклонение — в §
   2.1, неподтверждённое поле — в § 5.1.

### 7.4 Что проверять в первую очередь при обновлении

| Область               | Что искать                                                                                                                              |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Новые методы          | появление путей в `schema.yaml` → новая группа в § 4                                                                                    |
| Новые события         | `components.schemas` `*Update` — по одной схеме на тип события; сверить с нашим `Update`                                                |
| Лимиты и коды         | `/docs-api` (коды), `/docs-api/use-cases/sending-messages/media` (лимиты), `/docs-api/use-cases/sending-messages/keyboard` (клавиатура) |
| Удаления/депрекейшены | блок «Критически важные изменения» вверху `changelog-api`                                                                               |
| Тексты доки           | `/docs/changelog-platform`                                                                                                              |

---

## 8. Инварианты проекта (быстрая памятка)

- Base URL `https://platform-api2.max.ru`, авторизация — заголовок `Authorization: <access_token>`, лимит 30 RPS.
- Временные метки — **в миллисекундах**.
- Только официальная дока как источник истины; расхождение доки с API → фиксируется как «баг доки», **спека не
  «исправляется» под наблюдения живого API** (`AGENTS.md` § 3).
- Наблюдения с живого API и поведение клиентских пакетов — доказательства к задаче, не основание для правки спеки.
- Правки на русском; спека и справочник должны оставаться синхронными.
