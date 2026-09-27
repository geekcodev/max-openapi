# AGENTS.md — как работать с проектом max-openapi

## 1. Что это за проект

Неофициальная **OpenAPI 3.1.0 спецификация** Bot API мессенджера MAX: `openapi.yaml` + человекочитаемый справочник
`MAX_API_REFERENCE.md`. Спецификация составлена **только по официальной документации** `dev.max.ru` (см. § 3).

Твоя задача в будущих сессиях: быстро находить, куда смотреть, и корректно проверять/обновлять информацию, **не изучая
весь проект заново**.

> **Перед любой сверкой с доками открой `DOCS_MAP.md`** — это карта разделов и всех 32 методов с готовыми URL плюс
> регламент отслеживания релизов и список известных расхождений.

## 2. Состав репозитория

| Файл                   | Роль                                                                                                                                                       |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `openapi.yaml`         | Спека OpenAPI 3.1.0: 18 путей, 32 метода, 105 схем, 446 `$ref` на схемы/ответы/параметры                                                                   |
| `MAX_API_REFERENCE.md` | Человекочитаемый справочник (примеры, клавиатура, форматирование, вложения, request_contact)                                                               |
| `DOCS_MAP.md`          | разделы, 32 метода с URL, 11 объектов, регламент проверки релизов                                                                                          |
| `README.md`            | Ключевые факты API, команды проверки, инструкция по сертификатам НУЦ, покрытие                                                                             |
| `AGENTS.md`            | Этот файл: правила работы, ключевые факты API, сознательные отклонения (§2.1), реестр полей (§4.1), неподтверждённые факты (§5.1), регламент сверки (§7.1) |
| `LICENSE`              | MIT                                                                                                                                                        |
| `.gitignore`           | `.idea`                                                                                                                                                    |

### 2.1 Сознательные отклонения от официальной `schema.yaml` (не «ошибки» — не править при сверке)

| Отклонение                    | Официально                                                                                                                                                                                                            | У нас в спеке                                                                                                                                 | Решение                                                                                                                                                                                                                                                                        |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Имена подтипов `Update`       | `*Update` без базовой схемы                                                                                                                                                                                           | `UpdateBase` + `Update` (`oneOf` из 19 подтипов) + `Callback`; каждый подтип закрепляет `update_type` через `enum`, у каждого свой `examples` | 2026-09-27 — официальный `Update` не содержит `oneOf`, из-за чего `required` подтипов не проверяется валидатором; наша форма строже                                                                                                                                            |
| Имена подтипов вложений       | `ImageAttachment` (не `PhotoAttachment`)                                                                                                                                                                              | `PhotoAttachment` (совпадает с `PhotoAttachmentPayload`, фото-вложение)                                                                       | 2026-09-27 — выбрано имя, соответствующее типу `image` и уже существовавшей `PhotoAttachmentPayload`                                                                                                                                                                           |
| Расположение payload вложений | часть метаданных на верхнем уровне подтипа: `width`/`height`/`thumbnail`/`duration` (видео), `filename`/`size` (файл), `width`/`height` (стикер), `title`/`description`/`image_url` (превью), `transcription` (аудио) | те же поля внутри `payload` подтипа — набор и обязательность совпадают, отличается только место                                               | 2026-09-27 — сохранена существовавшая модель; официальные подтипы не объявляют `oneOf`, поэтому лишние поля в `payload` не ломают валидацию. **Проверено 2026-09-27:** покрытие полей всех 6 подтипов вложений полное, расхождений 0                                           |
| `payload` у `share`-запроса   | отдельный пустой `ShareAttachmentRequestPayload`                                                                                                                                                                      | используется `ShareAttachmentPayload` (`url` + `token`)                                                                                       | 2026-09-27 — иначе передать ссылку для превью нечем; `AGENTS.md` § 2.1                                                                                                                                                                                                         |
| `UploadedInfo.url`            | в `schema.yaml` только `token` (`readOnly`)                                                                                                                                                                           | `token` + `url`; `url` обязателен в ответе `POST /uploads`                                                                                    | 2026-09-27 — **подтверждено текстовой докой**: «В ответ на текущий запрос `POST /uploads` в поле `url` вернётся URL для загрузки медиафайла» (`https://dev.max.ru/docs-api/methods/POST/uploads`). Машинная схема поле не описывает — это не ошибка, а неполнота `schema.yaml` |
| `Callback`                    | `timestamp`, `callback_id`, `payload`, `user`; вложенного `message` нет                                                                                                                                               | те же 4 поля; `message` — на верхнем уровне `MessageCallbackUpdate` (Nullable)                                                                | 2026-09-27 — официальная форма, дублирование `message` устранено                                                                                                                                                                                                               |
| Версия OpenAPI                | 3.0.0                                                                                                                                                                                                                 | 3.1.0                                                                                                                                         | сознательно с самого начала; 2026-09-27 nullability переведена на 3.1-легальные формы — `type: [x, "null"]` (76) и `anyOf` с `- type: "null"` (19); ключевое слово `nullable` в 3.1 не существует, строгие тулы игнорировали бы его                                            |
| `required` для `Message.body` | обязателен, без `nullable`                                                                                                                                                                                            | обязателен, но nullable                                                                                                                       | 2026-09-27                                                                                                                                                                                                                                                                     |
| `User.name`                   | в `schema.yaml` отсутствует                                                                                                                                                                                           | оставлено в 4 схемах (`User`, `UserWithPhoto`, `BotInfo`, `ChatMember`) как deprecated                                                        | 2026-09-27 — **подтверждено текстовой докой**: страница `https://dev.max.ru/docs-api/objects/User` описывает `name` как «Устаревшее поле, скоро будет удалено»; то же в `UserWithPhoto`, `BotInfo`, `ChatMember` и в ответе `GET /me`                                          |

Полный список сознательных отклонений — в этой таблице; что осталось нерешённым — в § 5.1. Порядок работы со сверкой и
разбор её результатов — в § 7.1.

## 3. Источники истины (только эти, по порядку приоритета)

| Источник                                                      | Назначение                                                                                      |
|---------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `https://dev.max.ru/docs-api/changelog-api`                   | **Журнал релизов API** — первое, что проверять при обновлении                                   |
| `https://github.com/max-messenger/api-schema` → `schema.yaml` | **Официальная машинная спека.** Единственный источник правды по типам и полям объектов          |
| `https://dev.max.ru/docs-api`                                 | **Основной текстовый.** Методы: `/methods/<VERB>/<path>`, объекты: `/objects/<object>`, лимиты  |
| `https://dev.max.ru/docs-api/use-cases/*`                     | Сценарии: события, `chat_id`, команды, форматирование, вложения, клавиатура, медиа, комментарии |
| `https://dev.max.ru/docs`                                     | Платформа: боты, вебхуки, Long Polling, веб-приложения, каналы, Цифровой ID                     |
| `https://dev.max.ru/docs/webapps/validation`                  | WebAppData, `auth_date`, hash `request_contact`                                                 |
| `https://dev.max.ru/docs/webapps/bridge`                      | Бридж мини-приложений                                                                           |
| `https://dev.max.ru/docs/open-api`                            | Open Client API                                                                                 |
| `https://dev.max.ru/docs/changelog-platform`                  | История изменений платформы и текстов доки                                                      |

Полные URL всех страниц собраны в `DOCS_MAP.md` § 2–3.

**Правило — не выдумывать.** Каждый факт подтверждается цитатой из доки (URL + дата). Если факта в официальных доках
нет — он помечается как неподтверждённый, а не домысливается. Внешние источники (клиентские пакеты, живой API) не
используются — это вне скоупа проекта.

## 4. Ключевые факты API (обновлено 2026-09-27)

- Base URL: `https://platform-api2.max.ru` (не `platform-api.max.ru`), лимит **30 RPS**.
- Авторизация: заголовок `Authorization: <access_token>`; передача токена query-параметром **больше не поддерживается**.
- HTTPS обязателен (вебхуки только HTTPS), нужен сертификат Минцифры НУЦ — инструкция в README.
- Временные метки (timestamp, join_time и т.п.) — **в миллисекундах**.
- `GET /updates`: `limit` 1..1000 (default 100), `timeout` 0..90 (default 30), пагинация через `marker`; без `marker`
  возвращается только последнее обновление.
- `POST /messages`: `text` ≤ 4000 символов; не более 2 сообщений/сек.
- `PUT /messages`: редактирование до 7 дней в диалогах (кроме сообщений с `inline_keyboard`).
- Клавиатура: 210 кнопок / 30 рядов / 7 в ряд; спец-кнопки: link, open_app, request_geo_location, request_contact; текст
  кнопки ≤ 2048, link ≤ 2048.
- Загрузка файлов: домены `fu.oneme.ru`, `iu.oneme.ru`, `vu.okcdn.ru`; лимиты image 50 МБ / 7680×7680, video 250 МБ,
  audio 256 МБ / 60 мин, file 4 ГБ; resumable + multipart; error `attachment.not.ready`.
- Вебхуки (POST /subscriptions): тело `{url, update_types, secret}`, `secret` по паттерну `^[a-zA-Z0-9_-]{5,256}$`;
  доставка с заголовком `X-Max-Bot-Api-Secret`, HTTP 200 за 30 сек, ретраи 60→150→375 сек (×2.5), ~10 попыток до 8 ч,
  автоотписка после 8 ч. Параметра `allowed_hosts` нет.
- Update: 19 типов событий, 19 подтипов `*Update` (`UpdateType`); детально в доках расписан только пример `bot_added`, а
  `bot_admin_permissions_changed` есть только в официальной `schema.yaml` (`BotAdminPermissionsChangedUpdate`)
  (`update_type`, `timestamp`, `chat_id`, `user`, `is_channel`).
- Комментарии (август 2026): 5 методов `/messages/{messageId}/comments*`; комментарий создаётся только в канале
  (`recipient.chat_type: channel` + `recipient.post_id`); три события `comment_created` / `comment_edited` /
  `comment_removed` приходят боту **только с правом `read_all_messages`**.
- Subscription: `url` + `time` обязательны, `update_types` опционален; полей `type`/`state` нет ни в доках, ни в
  официальной `schema.yaml`.
- `PATCH /chats/{chatId}` принимает `description` (до 16000 символов).
- `POST /chats/{chatId}/members` удаляется **30.09.2026** (только страница метода; в `changelog-api` есть лишь
  ограничение с 09.09.2026, в официальной `schema.yaml` путь и операция ещё есть).
- Коды ошибок (общий список): 200, 400, 401, 404, 405, 429, 503.

### 4.1 Реестр полей `integer/int64` — строковые значения на живом API

**Правило: поля остаются `integer/int64` в спеке.** Основание: официальная `schema.yaml` объявляет идентификаторы явно —
`UserId` → `integer/int64`, `ChatId` → `integer/int64`, `bigint` → `integer/int64`, и только `MessageId` → `string`
(проверено 2026-09-27). Спека этому соответствует: `mid` — строка,
`chat_id`/`user_id` — числа.

Наблюдения с живого API идут как **доказательство к задаче**, а не как основание для правки спеки (§3).

| Где                                       | Наблюдение (2026-09-27)                                        |
|-------------------------------------------|----------------------------------------------------------------|
| `link.*` внутри сообщений                 | `mid`, `chat`, `sender` приходят **десятичными строками**      |
| `chat_id`, `user_id` в остальных объектах | приходят **числами** — расхождение локально для объекта `link` |
| `Marker` в `GET /updates`                 | число (соответствует спеке)                                    |

Следствие для клиентов (`geekcodev/max-php-client`): v1.1.3 падал с
`InvalidResponseException: Field "sender" must be an integer` после отправки сообщения (терялся `mid`, запрос уходил в
повтор) и отбрасывал апдейты с `message.link` (HTTP 400 на вебхуке); в v1.1.4 строковое значение допущено.

**Список полей `integer/int64` в `openapi.yaml` — сверять при каждой проверке одним проходом (45 в 33 схемах):**

| Схема                              | Поле                                     |
|------------------------------------|------------------------------------------|
| `BotAddedToChatUpdate`             | `chat_id`                                |
| `BotAdminPermissionsChangedUpdate` | `bot_id`, `chat_id`, `user_id`           |
| `BotRemovedFromChatUpdate`         | `chat_id`                                |
| `BotStartedUpdate`                 | `chat_id`                                |
| `BotStoppedUpdate`                 | `chat_id`                                |
| `Callback`                         | `timestamp`                              |
| `Chat`                             | `chat_id`, `last_event_time`, `owner_id` |
| `ChatAdmin`                        | `user_id`                                |
| `ChatMember`                       | `join_time`, `last_access_time`          |
| `ChatTitleChangedUpdate`           | `chat_id`                                |
| `CommentLinkedMessage`             | `chat_id`                                |
| `CommentMessage`                   | `timestamp`                              |
| `CommentMessageBody`               | `seq`                                    |
| `CommentRemovedUpdate`             | `chat_id`, `user_id`                     |
| `ContactAttachmentRequestPayload`  | `contact_id`                             |
| `DialogClearedUpdate`              | `chat_id`                                |
| `DialogMutedUpdate`                | `chat_id`, `muted_until`                 |
| `DialogRemovedUpdate`              | `chat_id`                                |
| `DialogUnmutedUpdate`              | `chat_id`                                |
| `FileAttachmentPayload`            | `size`                                   |
| `LinkedMessage`                    | `chat_id`                                |
| `Message`                          | `timestamp`                              |
| `MessageBody`                      | `seq`                                    |
| `MessageRemovedUpdate`             | `chat_id`, `user_id`                     |
| `PhotoAttachmentPayload`           | `photo_id`                               |
| `Recipient`                        | `chat_id`, `user_id`                     |
| `Subscription`                     | `time`                                   |
| `Update`                           | `timestamp`                              |
| `UpdateBase`                       | `timestamp`                              |
| `User`                             | `last_activity_time`, `user_id`          |
| `UserAddedToChatUpdate`            | `chat_id`, `inviter_id`                  |
| `UserMentionMarkup`                | `user_id`                                |
| `UserRemovedFromChatUpdate`        | `admin_id`, `chat_id`                    |

> `Update.timestamp` и `UpdateBase.timestamp` — одно и то же поле, объявленное в точке входа `Update`
> и в базе; в списке посчитаны оба объявления. До рефакторинга `Update` те же поля перечислялись
> на верхнем уровне `Update` — сверять список, а не текст.

**Параметры (14):** `components/parameters/chatId`; `DELETE /chats/{chatId}/members/admins/{userId}` → `userId`;
`GET /chats/{chatId}/members` → `marker`; `DELETE /chats/{chatId}/members` → `user_id`; `GET /updates` → `marker`;
`GET /messages` → `chat_id`, `from`, `to`, `after`, `before`; `POST /messages` → `user_id`, `chat_id`;
`GET /messages/{messageId}/comments` → `after`, `before`.

**Задачи на будущее:**

1. При следующей сверке проверить, не приходят ли строкой поля вне объекта `link` (особенно `marker` в
   `GET /updates` и `chat_id` в `Recipient`).
2. Если API начнёт отдавать ID строками — это будет изменение в официальной `schema.yaml`; тогда менять спеку и
   `MessageId`/`UserId`/`ChatId` в официальной схеме.
3. Формально-типовые расхождения держать в этом реестре, а не в разрозненных задачах.

## 5. Известные несоответствия в доках (баги доки — при сверке не править спецy)

- Объект `ChatMember`: на странице объекта enum из 13 прав (без `view_stats`), в разделе «Доступные права» — 11 + 3
  legacy (`post_edit_delete_message`, `edit_message`, `delete_message`). В спеке — 14 значений с пометкой deprecated.
- На страницах методов встречаются коды 403/500, которых нет в общем списке кодов — спека использует единый список.
- `POST /subscriptions`: в прозе написано «только A-Z, a-z, 0-9 и дефис», а в regex разрешён `_` — спека следует regex.
- `disable_link_preview`: в `schema.yaml` для `POST /messages` и `POST /messages/{messageId}/comments` описано «If
  `false`, server will not generate media preview», что противоречит `default: false` и смыслу имени параметра. Спека во
  всех трёх методах (`POST /messages`, `POST /answers`, `POST .../comments`) придерживается `true` = превью выключено.
  **Подтверждено 2026-09-27:** для `POST /answers` официальное описание сформулировано в правильном направлении — «If
  `true`, server will not generate media preview for links in updated message text», то есть расхождение относится
  только к формулировке двух других методов. Параметр объявлен официально во всех трёх методах (`type: boolean`,
  `default: false`) — покрытие спеки полное; запись в `changelog-api` за август 2026 (добавлен в `POST /answers`) уже
  отражена.
- `GET /chats`: в `changelog-api` помечен «Удалено» (июнь 2026), в официальной `schema.yaml` пути уже нет — спека
  приведена в соответствие, метод удалён (2026-09-27).
- `POST /chats/{chatId}/members`: дата удаления **30.09.2026** есть только на странице метода
  (`https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members`); в `changelog-api` упоминается только ограничение
  с 09.09.2026, в официальной `schema.yaml` путь и операция ещё есть без пометки. Спека приведена в соответствие
  досрочно (2026-09-27), в справочнике — раздел «Удалённые методы». Слов «deprecated»/«устарело» на странице метода
  нет — `deprecated: true` было наше решение по смыслу объявления.
- `User.name`: задокументировано на странице объекта как deprecated, но **отсутствует** в официальной `schema.yaml` —
  спека оставляет поле (опирается на текстовую доку).
- `Message.body`: текстовая дока допускает `body: null` для сообщений только из пересланного содержимого, а
  `schema.yaml` требует `body` и не объявляет его nullable — спека оставляет обязательным, но nullable.
- Миниатюра видео: `VideoAttachment.thumbnail` (вложение в сообщении) — официальная `schema.yaml` объявляет тип
  `VideoThumbnail` (только `url`), а `VideoAttachmentDetails.thumbnail` (ответ `GET /videos/{videoToken}`) — тип
  `PhotoAttachmentPayload`. Спека следует машинной схеме в обоих случаях: `VideoAttachmentPayload.thumbnail` →
  `VideoThumbnail`, `VideoInfo.thumbnail` → `PhotoAttachmentPayload`. Это не баг доки, а два разных контракта (проверено
  2026-09-27). Страница `GET /videos/{videoToken}` подтверждает оба (`urls`, `width`, `height`, `duration`).
- `ContactAttachmentPayload`: пример отправки контакта на странице use-case показывает поля `name` и `contact_id`,
  которых нет в `schema.yaml` (`vcf_info`, `hash`, `max_info`) — спека следует машинной схеме.

## 5.1 Неподтверждённые факты (в доках не найдены — не забывать, проверять при обновлении доков)

| # | Факт в спеке                                                                                                                        | Что в доках отсутствует                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|---|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Лимит `payload` кнопки — 8 КБ                                                                                                       | Явный лимит не документирован                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2 | ~~По-типовые поля Update~~                                                                                                          | **Закрыто 2026-09-27:** в официальной `schema.yaml` 19 специализированных `*Update`-схем, они и разложены у нас на 19 подтипов с `enum` по `update_type`; текстовая дока по-прежнему расписывает только `bot_added` (`bot_admin_permissions_changed` — только в машинной схеме)                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 3 | ~~Поля `type`/`state` Subscription~~                                                                                                | **Закрыто 2026-09-27:** в официальной `schema.yaml` таких полей нет; `url` + `time` обязательны, `update_types` опционален                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 4 | ~~`chat_type` в `Recipient`~~                                                                                                       | **Закрыто 2026-09-27:** значения `dialog`, `chat`, `channel` — в официальной `schema.yaml` (`ChatType`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 5 | ~~`LinkedMessage` как `sender: int`~~                                                                                               | **Закрыто 2026-09-27:** в официальной `schema.yaml` `sender` → объект `User`, поля `chat_id` + `message`; разобрано в `AGENTS.md` § 5.1 п. 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 6 | Вложенные объекты без страницы в доках (`MessageBody`, `MessageStat`, `Recipient`, `Attachment`, `NewMessageLink`, `LinkedMessage`) | Страниц объекта нет, но они описаны в официальной `schema.yaml` — использовать её. Для `MessageBody` страницы нет вообще: состав подтверждён машинной схемой и описанием `Message.body` на `https://dev.max.ru/docs-api/objects/Message` (проверено 2026-09-27)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 7 | ~~Поля, отсутствующие в `schema.yaml`, но оставленные в спеке~~                                                                     | **Закрыто 2026-09-27 (сверка с текстовой докой).** `MessageBody.caption` — **удалено**: `caption` не встречается ни в одной из 133 официальных схем, страница `Message` описывает `body` как «Содержимое сообщения. Текст + вложения». `MessageBody.format` — **удалено**: официально `format` объявлен только в `NewMessageBody` и `NewCommentBody` (тело запроса, `enum TextFormat` — `markdown`/`html`), а не в ответе; `markup` в ответе несёт уже разобранную разметку. `PhotoAttachmentPayload.width`/`height` — **удалено**: официальная схема объявляет габариты для видео и стикера, но сознательно не для фото, и страницы доков их не упоминают. **Неподтверждённых полей не осталось.** |
| 8 | `MarkupElement` + 10 подтипов без `discriminator`                                                                                   | В `schema.yaml` — `discriminator`/`oneOf`; наша форма компактнее и сознательна (`AGENTS.md` § 2.1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 9 | ~~`StickerAttachmentPayload` — пустой объект без полей~~                                                                            | **Закрыто 2026-09-27:** утверждение было неверным. Официальная `schema.yaml` объявляет `code` (обязательное) и наследует `url` из `AttachmentPayload`, а `StickerAttachment` требует `width` и `height`. Все четыре поля добавлены в `StickerAttachmentPayload`. `StickerAttachmentRequestPayload` официально содержит `code` (обязательное) и совпадает с нашим — расхождений нет                                                                                                                                                                                                                                                                                                                  |

## 5.2 Не покрыто спекой (добавлено в доках после 14.08.2026)

Сводка — в `DOCS_MAP.md` § 6. Статус на 2026-09-27: **всё закрыто**.

- ✅ группа **comments** — 5 методов, 6 схем, 3 события обновлений (закрыто 2026-09-27);
- ✅ `description` в `PATCH /chats/{chatId}` (закрыто 2026-09-27);
- ✅ `GET /chats` — удалён (июнь 2026, changelog; пути нет в `schema.yaml`): метод убран из спеки и справочника, добавлен
  раздел «Удалённые методы» (закрыто 2026-09-27).
- ✅ `POST /chats/{chatId}/members` — удаляется 30.09.2026 (объявлено на странице метода): операция `post` удалена
  досрочно 2026-09-27 вместе со схемой `FailedUserDetails`; путь `/chats/{chatId}/members` остался из-за `get`/`delete`.
  Ожидаемое расхождение с официальной `schema.yaml` — 1 операция, исчезнет после 30.09.2026.

## 6. Рабочий процесс: проверка информации или обновление

1. Открыть нужную страницу доки (URL из § 3), вытащить цитату и дату проверки.
2. Сверить сразу **оба** файла: `openapi.yaml` и `MAX_API_REFERENCE.md` — они должны оставаться синхронными.
3. Внести правки; если расхождение в самой доке — зафиксировать как «баг доки», а спецy оставить как есть.
4. Прогнать валидацию (команды ниже).
5. Обновить строку «Последнее обновление» в README (дата + подтверждающий источник).
6. Язык всех правок и описаний — **русский** (как в существующих файлах).

## 7. Проверка и валидация

```bash
# YAML-синтаксис
python3 -c "import yaml; yaml.safe_load(open('openapi.yaml')); print('OK')"

# Разрешение всех $ref (schemas + responses)
python3 -c "
import yaml, re
spec = yaml.safe_load(open('openapi.yaml'))
schemas = set(spec['components']['schemas'].keys())
responses = set(spec['components']['responses'].keys())
refs = re.findall(r'\"#/components/(schemas|responses)/(\w+)\"', open('openapi.yaml').read())
broken = [f'{t}/{n}' for t, n in refs if n not in (schemas if t == 'schemas' else responses)]
print(f'{len(refs)} refs, {len(broken)} broken' if broken else f'Все {len(refs)} ссылок резолвятся')
"

# Строгая проверка 3.1.0 (ловит 3.0.x-ключевые слова, например `nullable`)
python3 -m venv /tmp/opencode/.venv-oas && /tmp/opencode/.venv-oas/bin/pip install -q openapi-spec-validator
/tmp/opencode/.venv-oas/bin/python -c "
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
spec, _ = read_from_filename('openapi.yaml'); validate(spec); print('OpenAPI 3.1.0 валидна')
"

# Отсутствие дублей ключей YAML (важно: PySAML/парсер молча берёт последний)
python3 -c "
import yaml
class S(yaml.SafeLoader): pass
def nd(l, n, d=False):
    ks = []
    for k, _ in n.value:
        kk = l.construct_object(k, deep=d)
        if kk in ks: raise ValueError(f'дубль ключа {kk!r} (строка {k.start_mark.line+1})')
        ks.append(kk)
    return yaml.SafeLoader.construct_mapping(l, n, d)
S.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, nd)
yaml.load(open('openapi.yaml'), Loader=S); print('дублей ключей нет')
"
```

### 7.1 Разбор результатов сверки с `schema.yaml`

`schema.yaml` — единственный источник правды по типам и полям. Сверка выполняется так:

```bash
git clone --depth 1 https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official
python3 /tmp/opencode/diff_official.py    # скрипт живёт вне репозитория; пересоздать при смене окружения
```

**Ожидаемый результат на 2026-09-27** (официальная v0.0.33, коммит `1a4a502`): пути совпадают полностью (18 = 18);
операций официально на 1 больше (`POST /chats/{chatId}/members`, удаляется 30.09.2026); **схем нет у нас 42, лишних у
нас 14** — обе цифры разобраны по группам в `DOCS_MAP.md` § 1.

**Ложные срабатывания.** Скрипт не разворачивает `$ref` и `allOf`, поэтому часть вывода — артефакты, которые **не**
являются расхождениями спеки. Фильтровать вручную:

1. `components/parameters` — для всех 18 операций с `{chatId}`/`{messageId}` показывается «нет у нас
   `chatId` / лишние `#/components/parameters/chatId`. Параметры вынесены в `components/parameters` намеренно.
2. `FileAttachmentPayload: лишние у нас ['token', 'url']; required лишние ['token', 'url']` — официальная схема собирает
   их как `allOf: [$ref AttachmentPayload, {properties: {token}, required: [token]}]`, поэтому скрипт не видит ни `url`
   (из базы), ни `token` (из инлайн-части). Фактически оба поля официальны и обязательны.
3. `required` в подтипах вложений — проверяется после разворачивания `allOf`, иначе выглядит «лишним у нас» (то же
   касается `payload` в `*AttachmentRequest`).
4. **Половина официальных схем скрыта в `allOf`** — 52 из 90 общих схем объявляют поля только через `allOf`, поэтому
   скрипт их не видит вовсе. Из-за этого 2026-09-27 были пропущены поля `StickerAttachmentPayload.code`,
   `StickerAttachment.width`/`height`, `FileAttachment.filename`/`size`, `VideoAttachment.width`/`height`/`thumbnail`,
   `AudioAttachment.transcription`, `ShareAttachment.title`/`description`/`image_url` и `required` у `ChatMember` — все
   они добавлены. Сверять нужно компаратором, который разворачивает `allOf` **симметрично с обеих сторон**.

**Настоящие расхождения (не артефакты) — зарегистрированы, не «чинить».** Это поля, которых в официальной
`schema.yaml` нет вовсе; все прочие официальные поля присутствуют (проверено 2026-09-27 симметричным компаратором с
разворачиванием `allOf`):

| Схема                    | Поле                | Где зарегистрировано                                           |
|--------------------------|---------------------|----------------------------------------------------------------|
| `MessageBody`            | `caption`, `format` | § 5.1 п. 7 — не подтверждены `schema.yaml`                     |
| `PhotoAttachmentPayload` | `width`, `height`   | § 5.1 п. 7 — то же                                             |
| `User`                   | `name`              | § 5 — deprecated в текстовой доке, но нет в `schema.yaml`      |
| `UploadedInfo`           | `url`               | § 2.1 — нужен для загрузки, официальная схема его не описывает |

**14 лишних схем** — наши собственные базы и типы (`AttachmentBase`, `AttachmentRequestBase`,
`AttachmentType`, `UpdateBase`, `UpdateType`, `ButtonType`, `ErrorResponse`, `SuccessResponse`), подтипы вложений,
разложенные на `payload` (`AudioAttachmentPayload`, `InlineKeyboardAttachmentPayload`,
`VideoAttachmentPayload`), и `VideoInfo`. `Update`/`Callback` в diff больше не появляются: после добавления
`Update.properties` и переноса `message` в `MessageCallbackUpdate` они совпадают с официальной схемой по полям.

**Куда записывать результат сверки.** Отдельного файла со списком задач больше нет (`TODO.md` удалён 2026-09-27,
содержимое разложено по этому файлу): подтверждение сходит в § 4 и § 4.1; сознательно оставленное расхождение — в § 2.1;
поле без подтверждения в официальной схеме — в § 5.1, с пометкой в описании самой схемы. Наблюдения живого API — в § 4.1
как доказательства, а не как основание менять спеку (§ 3).

**Важно про nullability.** Ключевое слово `nullable` в OpenAPI 3.1 **не существует** (3.1 использует JSON Schema
2020-12) и инструментами не интерпретируется: `openapi-spec-validator` такую спеку **не отвергает**, но и `null` в этих
полях **отвергается** при валидации данных. Поэтому с 2026-09-27 nullability записывается только так:
`type: [x, "null"]`
для примитивов и `anyOf: [{$ref: X}, {type: "null"}]` для `$ref`/`allOf`. Возвращать `nullable: true` нельзя.

Технические оговорки: в окружении нет `rg` (использовать `grep`); конфигурация opencode в `~/.config/opencode/`.
