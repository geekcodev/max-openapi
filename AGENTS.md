# AGENTS.md — как работать с проектом max-openapi

## 1. Что это за проект

Неофициальная **OpenAPI 3.1.0 спецификация** Bot API мессенджера MAX: `openapi.yaml` + человекочитаемый справочник
`MAX_API_REFERENCE.md`. Спецификация составлена **только по официальной документации** `dev.max.ru` (см. § 3).

Твоя задача в будущих сессиях: быстро находить, куда смотреть, и корректно проверять/обновлять информацию, **не изучая
весь проект заново**.

> **Перед любой сверкой с доками открой `DOCS_MAP.md`** — это карта разделов и всех 33 методов с готовыми URL плюс
> регламент отслеживания релизов и список известных расхождений.

## 2. Состав репозитория

| Файл                   | Роль                                                                                                                                                       |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `openapi.yaml`         | Спека OpenAPI 3.1.0: 18 путей, 33 метода, 107 схем, 473 `$ref` (454 на схемы/ответы + 19 на параметры)                                                     |
| `MAX_API_REFERENCE.md` | Человекочитаемый справочник (примеры, клавиатура, форматирование, вложения, request_contact)                                                               |
| `DOCS_MAP.md`          | разделы, 33 метода с URL, 11 объектов, регламент проверки релизов                                                                                          |
| `README.md`            | Ключевые факты API, команды проверки, инструкция по сертификатам НУЦ, покрытие                                                                             |
| `QUALITY.md`           | Оценка качества спеки относительно официальной схемы и план развития (критерии, риски, приоритеты P0–P2)                                                   |
| `AGENTS.md`            | Этот файл: правила работы, ключевые факты API, сознательные отклонения (§2.1), реестр полей (§4.1), неподтверждённые факты (§5.1), регламент сверки (§7.1) |
| `LICENSE`              | MIT                                                                                                                                                        |
| `.gitignore`           | `.idea`, `__pycache__/`, `*.pyc`                                                                                                                           |
| `.agents/`             | Журнал сессий и планы: `journals/JOURNAL.md`, `journals/sessions/`, `plans/` — см. § 6.1                                                                   |
| `tools/`               | Компараторы сверки с `schema.yaml` и единая проверка `tools/check_spec.py` — см. § 7.1                                                                     |
| `.github/`             | CI: `.github/workflows/spec-check.yml` — `tools/check_spec.py` на push/PR и по расписанию — см. § 7.1                                                      |

### 2.1 Сознательные отклонения от официальной `schema.yaml` (не «ошибки» — не править при сверке)

| Отклонение                               | Официально                                                                                                                                                                                                            | У нас в спеке                                                                                                                                                                                     | Решение                                                                                                                                                                                                                                                                                                                                                                                                                 |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Имена подтипов `Update`                  | `*Update` без базовой схемы                                                                                                                                                                                           | `UpdateBase` + `Update` (`oneOf` из 19 подтипов, общие поля наследует из `UpdateBase` через `allOf`) + `Callback`; каждый подтип закрепляет `update_type` через `enum`, у каждого свой `examples` | 2026-09-27 — официальный `Update` не содержит `oneOf`, из-за чего `required` подтипов не проверяется валидатором; наша форма строже; 2026-10-20 поля вынесены в `UpdateBase` без дублирования                                                                                                                                                                                                                           |
| Имена подтипов вложений                  | `ImageAttachment` (не `PhotoAttachment`)                                                                                                                                                                              | `PhotoAttachment` (совпадает с `PhotoAttachmentPayload`, фото-вложение)                                                                                                                           | 2026-09-27 — выбрано имя, соответствующее типу `image` и уже существовавшей `PhotoAttachmentPayload`                                                                                                                                                                                                                                                                                                                    |
| Расположение payload вложений            | часть метаданных на верхнем уровне подтипа: `width`/`height`/`thumbnail`/`duration` (видео), `filename`/`size` (файл), `width`/`height` (стикер), `title`/`description`/`image_url` (превью), `transcription` (аудио) | те же поля внутри `payload` подтипа — набор и обязательность совпадают, отличается только место                                                                                                   | 2026-09-27 — сохранена существовавшая модель; официальные подтипы не объявляют `oneOf`, поэтому лишние поля в `payload` не ломают валидацию. **Проверено 2026-09-27:** покрытие полей всех 6 подтипов вложений полное, расхождений 0                                                                                                                                                                                    |
| `payload` у `share`-запроса              | отдельный пустой `ShareAttachmentRequestPayload`                                                                                                                                                                      | используется `ShareAttachmentPayload` (`url` + `token`)                                                                                                                                           | 2026-09-27 — иначе передать ссылку для превью нечем; `AGENTS.md` § 2.1                                                                                                                                                                                                                                                                                                                                                  |
| `UploadedInfo.url` и `UploadEndpoint`    | два объекта: `UploadedInfo` — только `token` (payload вложений `video`/`audio`/`file`); `UploadEndpoint` — `url` (`required`) + nullable `token`, ответ `POST /uploads`                                               | `UploadedInfo` — `token` + `url` (payload вложений); ответ `POST /uploads` — отдельная схема `UploadEndpoint` (`url` обязателен, `token` nullable)                                                | 2026-09-27 — **подтверждено текстовой докой**: «В ответ на текущий запрос `POST /uploads` в поле `url` вернётся URL для загрузки медиафайла» (`https://dev.max.ru/docs-api/methods/POST/uploads`). Машинная схема поле не описывает — это не ошибка, а неполнота `schema.yaml`; 2026-10-20 — `url` сделан обязательным в `UploadEndpoint` (как в официальной схеме), `UploadedInfo` сохранил `url` для payload вложений |
| `Callback`                               | `timestamp`, `callback_id`, `payload`, `user`; вложенного `message` нет                                                                                                                                               | те же 4 поля; `message` — на верхнем уровне `MessageCallbackUpdate` (Nullable)                                                                                                                    | 2026-09-27 — официальная форма, дублирование `message` устранено                                                                                                                                                                                                                                                                                                                                                        |
| Версия OpenAPI                           | 3.0.0                                                                                                                                                                                                                 | 3.1.0                                                                                                                                                                                             | сознательно с самого начала; 2026-09-27 nullability переведена на 3.1-легальные формы — `type: [x, "null"]` (76) и `anyOf` с `- type: "null"` (19); ключевое слово `nullable` в 3.1 не существует, строгие тулы игнорировали бы его                                                                                                                                                                                     |
| `required` для `Message.body`            | обязателен, без `nullable`                                                                                                                                                                                            | обязателен, но nullable                                                                                                                                                                           | 2026-09-27                                                                                                                                                                                                                                                                                                                                                                                                              |
| `User.name`                              | в `schema.yaml` отсутствует                                                                                                                                                                                           | оставлено в 4 схемах (`User`, `UserWithPhoto`, `BotInfo`, `ChatMember`) как deprecated                                                                                                            | 2026-09-27 — **подтверждено текстовой докой**: страница `https://dev.max.ru/docs-api/objects/User` описывает `name` как «Устаревшее поле, скоро будет удалено»; то же в `UserWithPhoto`, `BotInfo`, `ChatMember` и в ответе `GET /me`                                                                                                                                                                                   |
| `CommentMessage` в событиях комментариев | `CommentCreatedUpdate.message` / `CommentEditedUpdate.message` → общий `Message`                                                                                                                                      | `CommentMessage` — самостоятельный объект (нет `url`, тело — `CommentMessageBody`)                                                                                                                | 2026-10-20 — **подтверждено текстовой докой**: на `https://dev.max.ru/docs-api/use-cases/comment-moderation` событие несёт именно комментарий — «идентификатор изменённого комментария в поле `message.recipient.post_id`» и «текстом комментария в поле `body.text`»; официальная схема переиспользует общий `Message`                                                                                                 |

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

## 4. Ключевые факты API (обновлено 2026-10-19)

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
- Update: 19 типов событий, 19 подтипов `*Update` (`UpdateType`). С октября 2026 страница `Update` перечисляет все 19
  типов текстом, включая `bot_admin_permissions_changed` (доставляется только по вебхуку, в Long Polling недоступно), но
  свойства по-прежнему расписаны только для примера `bot_added`; состав полей — по официальной
  `schema.yaml` (`BotAdminPermissionsChangedUpdate`: `update_type`, `timestamp`, `chat_id`, `user`, `is_channel`)
  (проверено 2026-10-19).
- Комментарии (август 2026): 5 методов `/messages/{messageId}/comments*`; комментарий создаётся только в канале
  (`recipient.chat_type: channel` + `recipient.post_id`); три события `comment_created` / `comment_edited` /
  `comment_removed` приходят боту **только с правом `read_all_messages`**, в поле `message` — `CommentMessage`
  (см. § 2.1).
- Subscription: `url` + `time` обязательны, `update_types` опционален; полей `type`/`state` нет ни в доках, ни в
  официальной `schema.yaml`.
- `PATCH /chats/{chatId}` принимает `description` (до 16000 символов).
- `POST /chats/{chatId}/members` — **живой метод**: с 09.09.2026 работа ограничена; пометки об удалении 30.09.2026 в
  актуальной доке нет ни на странице метода, ни в `changelog-api` (проверено 2026-10-19), операция есть в официальной
  `schema.yaml`. Досрочное удаление операции из спеки (2026-09-27) отменено — операция и схема `FailedUserDetails`
  возвращены 2026-10-19.
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
- `POST /chats/{chatId}/members`: в сентябре 2026 на странице метода была пометка об удалении **30.09.2026**
  («с 9 сентября 2026 работа метода будет ограничена, а с 30 сентября 2026 он будет удалён»), по которой операция была
  удалена из спеки досрочно 2026-09-27. **2026-10-19:** на странице метода и в `changelog-api` осталась только
  ограничение с 09.09.2026, пометки об удалении нет, в официальной `schema.yaml` операция и `FailedUserDetails`
  присутствуют → операция возвращена в спецу (решение пользователя). Зафиксировано, чтобы метод не удалять повторно по
  устаревшей пометке.
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
- **Пробелы рендера страниц (обнаружены 2026-10-19).** На страницах методов/объектов не отображаются отдельные
  поля/параметры, которые есть в `schema.yaml`; спека следует машинной схеме, страницы неполны:
    - `GET /messages` — отрендерено 5 параметров, но не `after`/`before` (оба есть в `schema.yaml`, а в описаниях
      `from`/`to` прямо сказано «use after instead»/«use before instead»);
    - `POST /messages/{messageId}/comments` — не отрендерен query-параметр `disable_link_preview` (в `schema.yaml`
      есть);
    - `GET /messages/{messageId}/comments/{commentId}` — ответ отрендерен без поля `stat` (в `schema.yaml`
      `CommentMessage.properties.stat` есть);
    - `Chat.status` (`ChatStatus`) — на странице объекта 4 значения, в `schema.yaml` их 5, включая `suspended`
      (спека: `suspended` добавлен 2026-10-19);
    - `last_activity_time` (`User`/`UserWithPhoto`/`BotInfo`/`ChatMember`) — на страницах объекта без пометки
      `Nullable`, хотя оговорка «может не возвращаться, если скрыт онлайн-статус» есть, а в `schema.yaml` объявлено
      `nullable: true`
      (спека приведена к nullable 2026-10-19).
- `UserRemovedFromChatUpdate.admin_id`: `schema.yaml` объявляет поле не-nullable, но его же описание говорит «Can be
  null in case when user left chat» — спека оставляет nullable (по смыслу описания) (проверено 2026-10-19).
- **Расхождение источников (обнаружено 2026-10-20).** `POST /chats/{chatId}/members/admins`: на странице метода
  (`https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins`) в теле запроса указан необязательный
  `marker` (integer int64, Nullable — «указатель на следующую страницу данных»), но в `schema.yaml` тело — обёртка
  `ChatAdminsList` (`{admins}`, `required: [admins]`) без `marker`. Спека следует странице метода и оставляет `marker`
  необязательным; машинная схема, судя по всему, переиспользует ту же обёртку, что и `GET`. Тела запросов по имени схемы
  не видны — проверять компаратором `op_bodies_diff.py` (§ 7.1).
- **Расхождения на странице «Модерация комментариев» (обнаружены 2026-10-20).** На
  `https://dev.max.ru/docs-api/use-cases/comment-moderation`:
    - в шаге 3 третье событие названо `comment_removed`, а в шаге 4 того же текста то же событие — уже
      `comment_deleted`; в `schema.yaml` и в спеке — `comment_removed` (спека следует машинной схеме);
    - права в шаге 2 перечислены как `read_all_message` (единственное число), тогда как официально — `read_all_messages`
      (и в `schema.yaml`, и на остальных страницах; спека использует множественное число).

## 5.1 Неподтверждённые факты (в доках не найдены — не забывать, проверять при обновлении доков)

| # | Факт в спеке                                                                                                                        | Что в доках отсутствует                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|---|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Лимит `payload` кнопки — 8 КБ                                                                                                       | Явный лимит не документирован                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2 | ~~По-типовые поля Update~~                                                                                                          | **Закрыто 2026-09-27:** в официальной `schema.yaml` 19 специализированных `*Update`-схем, они и разложены у нас на 19 подтипов с `enum` по `update_type`. **Уточнено 2026-10-19:** страница `Update` в текстовой доке теперь перечисляет все 19 типов (включая `bot_admin_permissions_changed`, только по вебхуку), но свойства по-прежнему расписаны только для примера `bot_added`                                                                                                                                                                                                                                                                                                                |
| 3 | ~~Поля `type`/`state` Subscription~~                                                                                                | **Закрыто 2026-09-27:** в официальной `schema.yaml` таких полей нет; `url` + `time` обязательны, `update_types` опционален                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 4 | ~~`chat_type` в `Recipient`~~                                                                                                       | **Закрыто 2026-09-27:** значения `dialog`, `chat`, `channel` — в официальной `schema.yaml` (`ChatType`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 5 | ~~`LinkedMessage` как `sender: int`~~                                                                                               | **Закрыто 2026-09-27:** в официальной `schema.yaml` `sender` → объект `User`, поля `chat_id` + `message`; разобрано в `AGENTS.md` § 5.1 п. 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 6 | Вложенные объекты без страницы в доках (`MessageBody`, `MessageStat`, `Recipient`, `Attachment`, `NewMessageLink`, `LinkedMessage`) | Страниц объекта нет, но они описаны в официальной `schema.yaml` — использовать её. Для `MessageBody` страницы нет вообще: состав подтверждён машинной схемой и описанием `Message.body` на `https://dev.max.ru/docs-api/objects/Message` (проверено 2026-09-27)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 7 | ~~Поля, отсутствующие в `schema.yaml`, но оставленные в спеке~~                                                                     | **Закрыто 2026-09-27 (сверка с текстовой докой).** `MessageBody.caption` — **удалено**: `caption` не встречается ни в одной из 133 официальных схем, страница `Message` описывает `body` как «Содержимое сообщения. Текст + вложения». `MessageBody.format` — **удалено**: официально `format` объявлен только в `NewMessageBody` и `NewCommentBody` (тело запроса, `enum TextFormat` — `markdown`/`html`), а не в ответе; `markup` в ответе несёт уже разобранную разметку. `PhotoAttachmentPayload.width`/`height` — **удалено**: официальная схема объявляет габариты для видео и стикера, но сознательно не для фото, и страницы доков их не упоминают. **Неподтверждённых полей не осталось.** |
| 8 | `MarkupElement` + 10 подтипов без `discriminator`                                                                                   | В `schema.yaml` — `discriminator`/`oneOf`; наша форма компактнее и сознательна (`AGENTS.md` § 2.1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 9 | ~~`StickerAttachmentPayload` — пустой объект без полей~~                                                                            | **Закрыто 2026-09-27:** утверждение было неверным. Официальная `schema.yaml` объявляет `code` (обязательное) и наследует `url` из `AttachmentPayload`, а `StickerAttachment` требует `width` и `height`. Все четыре поля добавлены в `StickerAttachmentPayload`. `StickerAttachmentRequestPayload` официально содержит `code` (обязательное) и совпадает с нашим — расхождений нет                                                                                                                                                                                                                                                                                                                  |

## 5.2 Не покрыто спекой (добавлено в доках после 14.08.2026)

Сводка — в `DOCS_MAP.md` § 6. Статус на 2026-10-19: **всё закрыто**, новых пропусков после сверки нет.

- ✅ группа **comments** — 5 методов, 6 схем, 3 события обновлений (закрыто 2026-09-27);
- ✅ `description` в `PATCH /chats/{chatId}` (закрыто 2026-09-27);
- ✅ `GET /chats` — удалён (июнь 2026, changelog; пути нет в `schema.yaml`): метод убран из спеки и справочника, добавлен
  раздел «Удалённые методы» (закрыто 2026-09-27).
- ✅ `POST /chats/{chatId}/members` — операция `post` и схема `FailedUserDetails` **возвращены 2026-10-19**: пометка об
  удалении 30.09.2026 исчезла из доки (страница метода и `changelog-api` показывают только ограничение с 09.09.2026),
  официальная `schema.yaml` операцию содержит. Расхождение «на 1 операцию» устранено.

## 6. Рабочий процесс: проверка информации или обновление

1. Открыть нужную страницу доки (URL из § 3), вытащить цитату и дату проверки.
2. Сверить сразу **оба** файла: `openapi.yaml` и `MAX_API_REFERENCE.md` — они должны оставаться синхронными.
3. Внести правки; если расхождение в самой доке — зафиксировать как «баг доки», а спецy оставить как есть.
4. Прогнать проверки § 7 — одной командой `python3 tools/check_spec.py` (валидация + машинная сверка, § 7.1). Новое
   расхождение закрывается правкой спеки либо строкой в § 2.1 / § 5; зарегистрированные отклонения не «чинить».
5. Обновить строку «Последнее обновление» в README (дата + подтверждающий источник).
6. Язык всех правок и описаний — **русский** (как в существующих файлах).
7. Зафиксировать сессию в `.agents/journals/` (§ 6.1): файл сессии + строка в `JOURNAL.md` — без пропуска, если правки
   содержательные.

### 6.1 Журнал сессий `.agents/` (обязательно после содержательных правок)

После любой содержательной сессии (правки `openapi.yaml`, `MAX_API_REFERENCE.md`, `DOCS_MAP.md`, `README.md`, этого
файла) история фиксируется в каталоге `.agents/` — он **отслеживается в git** и коммитится наравне с остальными файлами
(untracked в нём быть не должно):

```
.agents/
├── journals/
│   ├── JOURNAL.md        # карта сессий: таблица Дата · Файл · Теги · Описание
│   └── sessions/         # по одному md-файлу на сессию: YYYY-MM-DD-тема.md
└── plans/                # планы многошаговых задач, статус: в работе / завершён / ждёт данных
```

**Файл сессии** `.agents/journals/sessions/YYYY-MM-DD-тема.md` — компактный отчёт:

- frontmatter: `tags: [ ... ]`, `date: YYYY-MM-DD`;
- секции `Проблема` / `Решение` / `Проверка` / `Нюансы` — что сделано, чем подтверждено, что осталось;
- обязательная строка о проверке: какие команды из § 7 прогонялись и с каким результатом; **цифры — из последнего
  прогона, а не из памяти**, незапущенный шаг честно отмечается как незапущенный;
- секреты, токены и живые payload в журнал не пишутся.

**`JOURNAL.md`** — по одной строке на сессию, новые сверху, колонки ровно такие:

| Дата       | Файл                                              | Теги             | Описание                                         |
|------------|---------------------------------------------------|------------------|--------------------------------------------------|
| YYYY-MM-DD | [YYYY-MM-DD-тема.md](sessions/YYYY-MM-DD-тема.md) | тег1, тег2, тег3 | краткое описание: что изменено, чем подтверждено |

- **Дата** — дата сессии (`YYYY-MM-DD`).
- **Файл** — ссылка на `.agents/journals/sessions/<имя файла>` (внутренняя ссылка, относительная).
- **Теги** — через запятую, по теме правок: `openapi`, `comments`, `docs`, `validation`, `fix`, `release` и т.п.
- **Описание** — 2–5 предложений по существу: что изменено, какой источник/дата подтверждения, какой результат проверки,
  что осталось незакрытым.

**Планы** — `.agents/plans/YYYY-MM-DD-тема.md` для задач из трёх и более шагов или требующих исследования (сверка с
доками, рефакторинг реестра полей): цель, шаги, нюансы, статус. Готовый план не удаляется, а помечается завершённым.

### 6.2 Общие правила работы

- **Не коммитить и не пушить без явного запроса** пользователя. `git add` — только после просмотра `git status` и
  `git diff`, не `git add .` наугад. «Напиши текст коммита» — вернуть строку-предложение, «закоммить» — выполнить
  `git commit`.
- Перед завершением задачи прогнать проверки из § 7 целиком (`python3 tools/check_spec.py`: валидация, `$ref`, дубли
  ключей, строгая 3.1.0, сверка отметки версии и три компаратора); результаты не подменять, недоступный шаг честно
  указать в отчёте и в файле сессии, а не пропускать молча.
- Та же проверка идёт в CI (`.github/workflows/spec-check.yml`, push/PR + расписание): красная сборка — повод разобрать
  новое расхождение или обновить отметку `info.x-official-schema`; вносить правки только после прогона локально.
- Если для задачи чего-то не хватает (нет доступа к докам, нет окружения) — сказать об этом, а не упрощать задачу молча.
- Ответы — краткие и по делу; все md-файлы и описания — на русском (§ 6 п. 6).

## 7. Проверка и валидация

Все проверки одной командой — `python3 tools/check_spec.py`: валидация ниже + три компаратора (§ 7.1) + сверка с
реестром зарегистрированных отклонений (`1` — есть новое расхождение, `2` — спека/окружение не прошли валидацию). Ниже —
те же проверки по отдельности.

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
python3 tools/check_spec.py   # валидация § 7 + сверка версии + все три компаратора + реестр зарегистрированных отклонений
```

**Компараторы живут в репозитории (`tools/`)** — при смене окружения пересоздавать нужно только клон официальной схемы и
venv с `openapi-spec-validator`, сами скрипты остаются. Актуальная версия разворачивает `$ref` и `allOf`
**симметрично с обеих сторон**:

- `tools/diff_official.py` — пути, операции, схемы (состав полей и `required`), параметры, `responses`, битые ссылки;
- `tools/op_bodies_diff.py` — тела запросов и 2xx-ответов **по смыслу**: официальные обёртки (`SendMessageResult`,
  `MessageList`, `ChatAdminsList`…) у нас записаны инлайн, поэтому обе стороны разворачиваются в плоский набор полей и
  `required` и сравниваются без учёта имён схем. Именно он видит то, что не видит сверка имён;
- `tools/types_diff.py` — типы/nullability/enum (разрешает `$ref` и `allOf`). Совместимые формы записи помечаются
  семейством (`alias` — псевдонимы скаляров `ChatId`/`UserId`, `format_uri`, `null_form`, `payload_relocation`) и в
  расхождения не засчитываются; настоящим считается только несовпадение `ref:`↔`ref:` двух разных схем (семейство
  `real`);
- `tools/check_spec.py` — единая команда: валидация § 7 + сверка версии + три компаратора + **реестр зарегистрированных
  отклонений** (список `REGISTERED` внутри файла). Итог делит найденное на «зарегистрированные» и «новые», а запись
  реестра без совпадений помечает как устаревшую; `--verbose` печатает все ключи;
- сверка полей **страниц доки** выполнялась разовыми скриптами (`fetch_docs_fields.py` → `compare_docs_vs_spec.py`); в
  репозитории они не хранятся — страницы генерируются из официальной спеки, поэтому машинная сверка их перекрывает.

**Отметка сверенной версии — `info.x-official-schema` в `openapi.yaml`.** Машинночитаемая привязка к официальной схеме,
чтобы «с чем сверено» не терялось и проверялось автоматически:

```yaml
info:
  version: 1.0.0                 # версия НАШЕЙ спеки (не путать)
  x-official-schema:
    version: "0.0.33"            # info.version официальной schema.yaml — жёсткая проверка
    commit: "1a4a502"            # коммит официального клона — справочно
    source: https://github.com/max-messenger/api-schema
    verified: "2026-10-20"
```

`tools/check_spec.py` сверяет `version` с `info.version` официальной схемы: расхождение — сигнал «официальная схема
обновилась, нужна сверка» (код возврата `1`, как у нового расхождения). `commit` и `verified` — справочные, на код
возврата не влияют: официальный репозиторий двигается чаще, чем меняется `version`. Обновлять `version`/`commit`/
`verified` при каждой завершённой сверке; в описании коммита указывать сверенную версию официальной схемы (релизов у
спеки нет, история — коммиты; `QUALITY.md` § 7).

**Та же проверка настроена в CI — `.github/workflows/spec-check.yml`**: push/PR, расписание (понедельник, 06:00 UTC) и
`workflow_dispatch`; шаги — Python 3.11, `pyyaml` + `openapi-spec-validator`, клон `api-schema` в `official-schema/`,
`OFFICIAL_SCHEMA` в переменных окружения, запуск `python3 tools/check_spec.py`. Красная сборка означает одно из трёх:
новое незарегистрированное расхождение (`1`), устаревшая отметка версии — официальная схема обновилась (`1`) или сбой
валидации/отсутствие официальной схемы (`2`).

**Ожидаемый результат на 2026-10-20** (официальная v0.0.33, коммит `1a4a502` — не менялась с 2026-09-27): пути совпадают
полностью (18 = 18); **операции совпадают** (после возвращения `POST /chats/{chatId}/members`, § 5/§ 5.2); **схем нет у
нас 40, лишних у нас 14** — обе цифры разобраны по группам в `DOCS_MAP.md` § 1. Поля и
`required`: все официальные поля присутствуют (проверено симметричным компаратором с разворачиванием `allOf`).

> **Подтверждено 2026-10-20** после пересоздания компараторов (окружение сброшено, официальная схема не менялась):
> выводы — `/tmp/opencode/diff_2026-10-20.txt` и `/tmp/opencode/types_2026-10-20.txt`; пути 18 = 18, операции 33 = 33,
> схем нет у нас 40, лишних 14, битых ссылок нет. Пересозданный `types_diff.py` дополнительно показывает строку
> `Message.body` (§ 2.1 — обязателен, но nullable), которую прошлая версия не выводила; расхождения — только
> зарегистрированные. **Дополнено тем же днём:** `op_bodies_diff.py` до фиксов показывал 2 реальных расхождения и
> 8 необязательных `required`; все исправлены (см. § 2.1 и журнал сессии `2026-10-20-body-level-fixes.md`).
> **Позже тем же днём:** компараторы перенесены в `tools/`; единая команда `python3 tools/check_spec.py` печатает
> валидацию, три отчёта и итог с реестром — на 2026-10-20 это **103 зарегистрированных отклонения, новых 0**
> (включая `CommentMessage` в событиях комментариев — зарегистрировано в § 2.1).

**Остаточные артефакты вывода** (не расхождения спеки):

1. `components/parameters` — для операций с `{chatId}`/`{messageId}` показывается «нет у нас `chatId` / лишние
   `#/components/parameters/chatId`»: параметры вынесены в `components/parameters` намеренно.
2. Строки `type_noise` в `types_diff.py` — сравнение «как записан тип»: официальная схема часто описывает поле через
   `allOf: [$ref ...]` или псевдоним скаляра, отсюда `офиц[any]`/`офиц[null]` против нашего явного типа. Каждая строка
   помечена семейством (`alias`, `format_uri`, `null_form`, `payload_relocation`) — в расхождения идут только строки
   блока «ТИПЫ — РАСХОЖДЕНИЯ» и итоговые блоки `NULLABILITY`/`ENUM`.
3. Порядок значений `enum` (`Chat.type`, `Recipient.chat_type`) — не расхождение; в отчёте помечен как `enum_order`.

> **История.** Первая версия скрипта не разворачивала `allOf`, из-за чего «половина схем была невидима»: 2026-09-27
> были пропущены `StickerAttachmentPayload.code`, `StickerAttachment.width`/`height`, `FileAttachment.filename`/`size`,
> `VideoAttachment.width`/`height`/`thumbnail`, `AudioAttachment.transcription`,
> `ShareAttachment.title`/`description`/`image_url` и `required` у `ChatMember` — все они тогда добавлены.

**Настоящие расхождения (не артефакты) — зарегистрированы, не «чинить».** Это поля, которых в официальной
`schema.yaml` нет вовсе; все прочие официальные поля присутствуют (проверено 2026-10-20 симметричным компаратором с
разворачиванием `allOf`):

| Схема                                          | Поле      | Где зарегистрировано                                                             |
|------------------------------------------------|-----------|----------------------------------------------------------------------------------|
| `User`                                         | `name`    | § 5 — deprecated в текстовой доке, но нет в `schema.yaml`                        |
| `UploadedInfo`                                 | `url`     | § 2.1 — payload вложений; ответ `POST /uploads` описан как `UploadEndpoint`      |
| `CommentCreatedUpdate` / `CommentEditedUpdate` | `message` | § 2.1 — событие несёт `CommentMessage`, официальная схема ссылается на `Message` |

Тела запросов и 2xx-ответов, где расхождение по **полям**, а не по именам схем, проверяются `op_bodies_diff.py`.
Зарегистрированное отклонение там одно: `marker` в теле `POST /chats/{chatId}/members/admins` (§ 5 — страница метода его
документирует, машинная схема нет).

Бывшие строки `MessageBody.caption`/`format` и `PhotoAttachmentPayload.width`/`height` убраны: эти поля удалены из спеки
2026-09-27 (§ 5.1 п. 7), и в текущем diff их нет.

**Nullability/enum приведены к `schema.yaml` 2026-10-19** (официальная схема — источник правды по типам, § 3):
`last_activity_time` в `User`/`UserWithPhoto`/`BotInfo`/`ChatMember` — nullable; `NewMessageBody.format` — nullable;
`user_locale` в `bot_started`/`bot_stopped`/`dialog_cleared`/`dialog_muted`/`dialog_unmuted`/`dialog_removed` — не
nullable; `Callback.payload`, `LinkedMessage.chat_id`, `CommentLinkedMessage.chat_id`, `UploadedInfo.token` — не
nullable; в `ChatStatus` добавлено значение `suspended`. Сознательных отклонений по nullability **два**:
`Message.body` (§ 2.1 — обязателен, но nullable: текстовая дока допускает `body: null`) и
`UserRemovedFromChatUpdate.admin_id` (§ 5: официальная схема не-nullable, но её описание допускает `null`).

**14 лишних схем** — наши собственные базы и типы (`AttachmentBase`, `AttachmentRequestBase`,
`AttachmentType`, `UpdateBase`, `UpdateType`, `ButtonType`, `ErrorResponse`, `SuccessResponse`), подтипы вложений,
разложенные на `payload` (`AudioAttachmentPayload`, `InlineKeyboardAttachmentPayload`,
`VideoAttachmentPayload`), и `VideoInfo`. `Update`/`Callback` в diff больше не появляются: у `Update` состав полей и
`required` те же, что у официальной схемы (общие поля наследуются из `UpdateBase` через `allOf`, 2026-10-20), а
`message` перенесён в `MessageCallbackUpdate`.

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
