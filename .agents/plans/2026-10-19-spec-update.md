# План обновления спеки max-openapi (запущен 2026-10-19)

**Статус 2026-10-19: все этапы 0–6 выполнены, открытых вопросов нет.** Журнал сессии —
`.agents/journals/sessions/2026-10-19-spec-actualization.md`. Осталось отслеживать: новые релизы в `changelog-api`
и возможное возвращение пометки об удалении `POST /chats/{chatId}/members` (§ 5).

**Цель:** привести `openapi.yaml` и `MAX_API_REFERENCE.md` к актуальным официальным источникам (`schema.yaml` +
текстовая дока `dev.max.ru`), обновить сопроводительные документы, прогнать валидацию.

**Правила движения по плану:**

- Пункты отмечаются `[x]` **сразу после выполнения**, с комментарием-доказательством (URL + дата, цифры из последнего
  прогона) прямо в пункте.
- При обрыве сессии продолжать со **первого неотмеченного** пункта; выполненное не перепроверять заново без основания.
- Источники истины — `AGENTS.md` § 3; сознательные отклонения не «чинить» (§ 2.1); баги доки фиксировать, а не
  переносить в спецу (§ 5).
- После содержательных правок — журнал сессии (`AGENTS.md` § 6.1), пункт этапа 6.
- Язык — русский.

**Исходные данные разведки (2026-10-19):**

- Официальная `schema.yaml`: коммит `1a4a502` от 2026-09-18 (v0.0.33) — **не менялся** с прошлой сверки 2026-09-27
  (`git ls-remote` HEAD тот же).
- `changelog-api`: новых записей с 2026-09-27 две, обе в разделе **Bots, октябрь 2026**:
    1. навык MAX Messenger Agent Skill (к спеке не относится);
    2. событие `bot_admin_permissions_changed` **добавлено в текстовую доку** (страница `Update` перечисляет все 19
       типов событий; свойства по-прежнему расписаны только для примера `bot_added`).
- `POST /chats/{chatId}/members`: дата удаления 30.09.2026 **прошла**, но метод жив и в доке, и в `schema.yaml`
  — открытый вопрос (этап 3).
- Глубина проверки текстовых страниц — **полный проход** (решение пользователя).

---

## Этап 0. Разведка — ВЫПОЛНЕН

- [x] `changelog-api` прочитан (https://dev.max.ru/docs-api/changelog-api, 2026-10-19): октябрьские записи —
  `bot_admin_permissions_changed` в текстовой доке + agent skill; больше изменений API нет.
- [x] `schema.yaml` обновлена до HEAD: не изменилась (коммит `1a4a502`, 2026-09-18).
- [x] Страница `objects/Update` (2026-10-19): все 19 типов событий перечислены текстом, включая
  `bot_admin_permissions_changed` (Webhook-only, для Long Polling недоступно). Свойства объекта по-прежнему расписаны
  только для `bot_added`.
- [x] Страница `POST /chats/-chatId-/members` (2026-10-19): метод жив, есть в сайдбаре, из пометок только «С 9 сентября
  2026 работа метода ограничена».
- [x] `changelog-platform` (https://dev.max.ru/docs/changelog-platform, 2026-10-19): изменений Bot API нет (только MAX
  Bridge `window.WebApp.PermissionsManager` для мини-приложений — вне скоупа).

## Этап 1. Машинная сверка со `schema.yaml` — ВЫПОЛНЕН

- [x] Компаратор пересоздан вне репозитория: `/tmp/opencode/diff_official.py` (состав полей/`required`) и
  `/tmp/opencode/types_diff.py` (типы/nullability/enum) — оба **симметричные, с разворачиванием `allOf`/`$ref`
  с обеих сторон**.
- [x] Прогон выполнен, вывод сохранён: `/tmp/opencode/diff_2026-10-19.txt`, `/tmp/opencode/types_2026-10-19.txt`.
- [x] Вывод разобран. Итог сверки:
  - **пути 18 = 18**; операции **до возврата `POST /chats/{chatId}/members` были на 1 меньше** — после возврата (этап 3)
  сходятся **33 = 33** (проверено повторным прогоном 2026-10-19); - **схемы: официально 133, у нас 106** (105 +
  возвращённый `FailedUserDetails`); нет у нас 41, лишних у нас 14 — **те же группы, что в § 7.1** (наши
  базы/подтипы/типы + встроенные обёртки `ModifyMembersResult`,
  `ChatMembersList`, `UserIdsList`), новых расхождений нет; - **поля и `required`: все официальные поля присутствуют у
  нас**; расхождения — зарегистрированные (payload-раскладка вложений § 2.1, `User.name` и `UploadedInfo.url` § 5.1)
  плюс **устаревшие записи § 7.1**: `MessageBody.caption`/`format` и `PhotoAttachmentPayload.width`/`height` у нас уже
  удалены и в diff не фигурируют — таблицу «настоящих расхождений» в § 7.1 надо актуализировать; - **артефакты** (не
  расхождения): `components/parameters` (официально инлайн), `allOf`-заглушки в типах, порядок значений enum
  `Chat.type`/`Recipient.chat_type`.
- [x] Реестр `integer/int64` (§ 4.1) пересчитан: **45 объявленных полей в 33 схемах** — совпадает с § 4.1, пополнения не
  требуется; параметров 14 (без изменений).
- [x] **Новые настоящие расхождения (16 nullability + 1 enum)** — найдены `types_diff.py`, требуют правки спеки (см.
  «Список правок» ниже). Официальная схема — источник правды (§ 3), поэтому приводим к ней.

## Этап 2. Полный проход текстовых страниц доки — ВЫПОЛНЕН

Метод-страницы проверены **автоматически**: HTML всех 33 страниц методов разобран
(`/tmp/opencode/fetch_docs_fields.py` → `/tmp/opencode/docs_fields.json`), из них извлечены параметры, поля тела и
ответа, затем сверены с нашим `openapi.yaml` (`/tmp/opencode/compare_docs_vs_spec.py`).

- [x] bots (2): `GET /me`, `PATCH /me/commands` — поля совпадают.
- [x] chats (14): `GET/PATCH /chats/{id}`, `POST .../actions`, `GET/PUT/DELETE .../pin`,
  `GET/DELETE .../members/me`, `GET/POST .../members/admins`, `DELETE .../admins/{userId}`,
  `GET/POST/DELETE .../members` — совпадают (возврат `POST .../members` — этап 3).
- [x] subscriptions (4): `GET/POST/DELETE /subscriptions`, `GET /updates` — совпадают; страница
  `POST /subscriptions` подтверждает `secret` (заголовок `X-Max-Bot-Api-Secret`), ретраи 60→150→375 сек и «до 8 часов» —
  сходится с § 4.
- [x] upload (1): `POST /uploads` — совпадает.
- [x] messages (7): `GET/POST/PUT/DELETE /messages`, `GET /messages/{id}`, `GET /videos/{token}`, `POST /answers`
  — совпадают, кроме `after`/`before` (см. таблицу).
- [x] comments (5): все `GET/POST/PUT/DELETE /messages/{id}/comments*` — совпадают, кроме `disable_link_preview`
  и `stat` (см. таблицу).
- [x] объекты (11): страницы `User`, `UserWithPhoto`, `BotInfo`, `ChatMember`, `Chat`, `Message`,
  `CommentMessage`, `NewMessageBody`, `NewCommentBody`, `Update` разобраны (`/tmp/opencode/objects_diff.py`,
  `/tmp/opencode/docs_txt/`) — состав полей совпадает с `schema.yaml`; подтверждены пометки `Nullable`/`optional`.
- [x] Страницы use-case просмотрены (тексты в `/tmp/opencode/docs_txt/`): `keyboard` (210 кнопок / 30 рядов / 7 в ряд),
  `media` (лимиты 50 МБ / 7680 / 250 МБ / 256 МБ / 4 ГБ), `comment-moderation`
  (`read_all_messages`), `text-formatting`, `attachment-types`, `another-attachments`, `chatbot-commands`,
  `getting-chat-id`, `event-notifications` — расхождений с § 4 (ключевые факты) не найдено.
- [x] Сводная таблица расхождений (URL + дата 2026-10-19):

| Что в доке                                                                                                                                                                | Что у нас                                          | Решение                                                                                                                                                       |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET /messages`: страница рендерит только `chat_id`, `count`, `from`, `to`, `message_ids`                                                                                 | 7 параметров, включая `after`/`before`             | `after`/`before` **есть в `schema.yaml`** (и в описаниях `from`/`to` — «use after instead») → у нас верно, пробел рендера страницы; занести в `AGENTS.md` § 5 |
| `POST /messages/{messageId}/comments`: `disable_link_preview` не отрендерен                                                                                               | параметр есть                                      | Параметр **есть в `schema.yaml`** → у нас верно, пробел доки; § 5                                                                                             |
| `GET /messages/{messageId}/comments/{commentId}`: `stat` не отрендерен                                                                                                    | поле `stat` есть (наследуется из `CommentMessage`) | **Есть в `schema.yaml`** (`CommentMessage.properties.stat`) → у нас верно, пробел доки; § 5                                                                   |
| `Chat.status` на странице `Chat`: значения `active`/`removed`/`left`/`closed`                                                                                             | 4 значения                                         | В `schema.yaml` (`ChatStatus`) — **5 значений, включая `suspended`** → **добавить в спеку**, пробел доки; § 5                                                 |
| `last_activity_time` на страницах `User`/`UserWithPhoto`/`BotInfo`/`ChatMember`: без пометки `Nullable`, но с оговоркой «может не возвращаться, если скрыт онлайн-статус» | не nullable                                        | В `schema.yaml` — **`nullable: true`** → **привести к nullable**; § 5                                                                                         |
| `MessageLinkType` (`NewMessageLink`/`LinkedMessage`/`CommentLinkedMessage`)                                                                                               | enum `forward`/`reply`                             | совпадает — правок нет                                                                                                                                        |
| `Update`: 19 типов событий, включая `bot_admin_permissions_changed` (Webhook-only)                                                                                        | 19 значений `UpdateType`                           | совпадает; **поправить формулировки** в `AGENTS.md` § 4 и § 5.1 п. 2 («только в `schema.yaml`» — устарело)                                                    |
| `POST /chats/{chatId}/members`                                                                                                                                            | операция удалена досрочно                          | **этап 3**: пометки об удалении в доке нет → операция возвращена                                                                                              |

## Этап 3. Открытый вопрос: `POST /chats/{chatId}/members` — ВЫПОЛНЕН

Решение пользователя: «сначала выяснить у доков» — не править спецу, пока не выяснено.

- [x] `changelog-platform` проверен (2026-10-19) — отмены удаления/новых ограничений нет.
- [x] Страница метода перечитана целиком (2026-10-19): **единственная пометка — «С 9 сентября 2026 работа метода
  `POST /chats/{chatId}/members` ограничена»**, слов об удалении нет; метод в сайдбаре, тело/параметры/ответы на месте.
- [x] `changelog-api`, раздел «Критически важные изменения»: « **С 9 сентября 2026** ограничена работа метода
  `POST /chats/{chatId}/members`» — про удаление 30.09.2026 ничего нет; в разделе Chats — только «Изменено» за сентябрь.
- [x] Wayback (CDX, 2026-10-19): последний снимок страницы метода — 2026-06-08, снимков периода сентябрь/октябрь 2026
  нет, поэтому появление/исчезновение пометки архивно не подтверждается. Решающим считаем **актуальное состояние доки +
  официальную `schema.yaml`** (обе содержат метод).
- [x] **Решение пользователя: вернуть операцию в спеку.** Внесено: `post` в `/chats/{chatId}/members` + схема
  `FailedUserDetails` (состав полей приведён к официальной: `error_code` + `user_ids`) + раздел 15 в
  `MAX_API_REFERENCE.md` (перенумерация: TOC 15–59 и заголовки методов 15–27 → 16–28, якоря обновлены; строка об
  удалении метода убрана из раздела «Удалённые методы») +
  `AGENTS.md` § 4/§ 5/§ 5.2/§ 7.1 + `DOCS_MAP.md` (§ 1, § 4, § 6, § 7.2). После правки операции совпадают **33 = 33**,
  схем нет у нас **41**.

## Этап 4. Правки спеки и справочника — ВЫПОЛНЕН 2026-10-19

**Список правок (этап 1/2, к `openapi.yaml`, зеркально в `MAX_API_REFERENCE.md`):**

1. `ChatStatus`: добавить `suspended` (официально 5 значений).
2. `User.last_activity_time`: `type: [integer, "null"]` (наследуется `UserWithPhoto`, `BotInfo`, `ChatMember`);
   поправить пояснение в `description` схемы `User`.
3. `NewMessageBody.format`: сделать nullable (`anyOf` + `type: "null"`) — как в `NewCommentBody.format`.
4. `user_locale` в 6 схемах (`BotStartedUpdate`, `BotStoppedUpdate`, `DialogClearedUpdate`, `DialogMutedUpdate`,
   `DialogUnmutedUpdate`, `DialogRemovedUpdate`): убрать null (официально `string` не nullable). В
   `MessageCreatedUpdate`/`MessageEditedUpdate` nullable **оставить** (официально nullable).
5. `Callback.payload`: убрать null (официально `string`, не в `required`).
6. `LinkedMessage.chat_id`, `CommentLinkedMessage.chat_id`: убрать null (официально `integer`).
7. `UploadedInfo.token`: убрать null (официально `string`).
8. `UserRemovedFromChatUpdate.admin_id`: **оставить nullable** — официальная схема объявляет не-nullable, но её же
   описание говорит «Can be null in case when user left chat»; зафиксировать как расхождение в § 5.

- [x] Внести правки 1–8 в `openapi.yaml` **и** в `MAX_API_REFERENCE.md` (§ 6 п. 2); сознательные отклонения (§ 2.1) не
  трогать, баги доки — в § 5. **Сделано 2026-10-19**; в справочнике дополнительно поправлены строки `last_activity_time`
  (GET /me, ChatMember, объект User), `status` (GET /chats/{id} и объект Chat),
  `user_locale`, `callback`, `chat_id` у `LinkedMessage`, `token` у `UploadedInfo`, примечание про
  `bot_admin_permissions_changed`.
- [x] Обновить `AGENTS.md`: § 4 (формулировка про `bot_admin_permissions_changed`), § 5.1 п. 2 (то же), § 5 (новые
  строки: пробелы рендера доки — `after`/`before`, `disable_link_preview`, `stat`, `suspended`,
  `last_activity_time`; `admin_id`), § 5.2/§ 6 (статус `POST .../members`), § 7.1 (таблица настоящих расхождений —
  убраны устаревшие строки `MessageBody`/`PhotoAttachmentPayload`, добавлен блок про приведение nullability/enum,
  компараторы). Также § 1/§ 2 (счётчики: 33 метода, 106 схем, 454 `$ref`).
- [x] Обновить `DOCS_MAP.md`: «Состояние карты» (дата 2026-10-19), § 1 (106 схем, нет у нас 41), § 4 (chats 14, строка
  POST .../members), § 6 (сводка + отмена удаления метода), § 7.2 (ожидаемый результат).
- [x] Обновить `README.md`: строка «Последнее обновление» (дата + источник), счётчики 33 метода/106 схем.

## Этап 5. Валидация (`AGENTS.md` § 7, все 4 команды) — ВЫПОЛНЕН 2026-10-19

- [x] YAML-синтаксис → `OK`.
- [x] Разрешение всех `$ref` → **Все 454 ссылок резолвятся**, 0 broken.
- [x] Строгая проверка OpenAPI 3.1.0 (`openapi-spec-validator`) → `OpenAPI 3.1.0 валидна`.
- [x] Отсутствие дублей ключей YAML → `дублей ключей нет`.
- [x] Цифры последнего прогона — в журнал сессии и в этот план (выше).

## Этап 6. Финализация

- [x] `git status --short` просмотрен 2026-10-19: изменены `AGENTS.md`, `DOCS_MAP.md`, `MAX_API_REFERENCE.md`,
  `README.md`, `openapi.yaml`, `.agents/journals/JOURNAL.md`; untracked — файл сессии и каталог `.agents/plans/`.
  Коммит — только по явному запросу пользователя (`AGENTS.md` § 6.2), не выполнялся.
- [x] Этот план: все этапы 0–6 отмечены, открытых вопросов не осталось.
- [x] Журнал сессии: `.agents/journals/sessions/2026-10-19-spec-actualization.md` + строка в `JOURNAL.md` (§ 6.1).

---

## Дополнение 2026-10-20 (запрос пользователя по отличию № 2)

- [x] `Update`: общие поля и `required` вынесены в `UpdateBase` и наследуются через `allOf` — дублирование убрано,
  состав/`oneOf`/`discriminator` не менялись. Поведение проверено (`required` доезжает через `allOf`, `oneOf`
  по-прежнему прибивает подтип, закрытый `enum` отклоняет неизвестный тип события).
- [x] Окружение пересоздано после сброса: клон официальной схемы (`1a4a502`, v0.0.33 — не менялась), компараторы
  `diff_official.py` / `types_diff.py` (§ 7.1), venv с `openapi-spec-validator`.
- [x] `AGENTS.md` § 2.1 (строка про `Update`) и § 7.1 (блок подтверждения 2026-10-20, источник строк `тип:`, два
  нуллабилити-отклонения вместо одного) обновлены.
- [x] Журнал: `.agents/journals/sessions/2026-10-20-update-allof.md` + строка в `JOURNAL.md`.
- Цифры на момент того шага: пути 18 = 18, операции 33 = 33, схем нет у нас 41 / лишних 14, битых ссылок нет,
  nullability-расхождений 2 (оба зарегистрированы), enum-расхождений 0, все 454 `$ref` резолвятся (после правок ниже —
  40/14, см. следующее дополнение).

---

## Дополнение 2026-10-20 (сверка тел запросов и ответов «по смыслу»)

- [x] Новый компаратор `/tmp/opencode/op_bodies_diff.py`: официальные обёртки (`SendMessageResult`, `MessageList`,
  `ChatAdminsList`, `CallbackAnswer`…) у нас записаны инлайн, поэтому сравниваются плоские наборы полей и
  `required`, а не имена схем (`AGENTS.md` § 7.1).
- [x] Исправлено в `openapi.yaml`: `notification` в `POST /answers`; `required` (`success`, `messages`, `message`,
  `updates`, `subscriptions`, `members`); новая схема `UploadEndpoint` (обязательный `url`) для `POST /uploads`.
- [x] `marker` в теле `POST /chats/{chatId}/members/admins` оставлен: страница метода его документирует, машинная схема
  (`ChatAdminsList`) — нет; зарегистрировано в `AGENTS.md` § 5 как расхождение источников.
- [x] Исправлены ошибки таблицы `DOCS_MAP.md` § 1: `VideoAttachmentDetails` вместо несуществующего
  `ShareAttachmentRequestPayload`, `ModifyMembersResult` вместо `ModifyResults`, убрана устаревшая строка
  `FailedUserDetails`; цифры 106 → 107 / 41 → 40.
- [x] Синхронизированы `MAX_API_REFERENCE.md` (тело и ответ `POST /answers`, ответ `POST /uploads`, раздел
  `UploadedInfo`) и `README.md`.
- [x] Журнал: `.agents/journals/sessions/2026-10-20-body-level-fixes.md` + строка в `JOURNAL.md`.
- Цифры после правок: 18 = 18 путей, 33 = 33 операции, официально 133 / у нас 107 схем (нет у нас 40, лишних 14), битых
  ссылок нет, все 454 `$ref` резолвятся; `op_bodies_diff` — только зарегистрированные отклонения.

---

## Дополнение 2026-10-20 (компараторы в репозитории, `check_spec.py`, регистрация расхождений)

- [x] Компараторы перенесены из `/tmp/opencode/` в `tools/` (`_common.py`, `diff_official.py`, `types_diff.py`,
  `op_bodies_diff.py`) — сверка воспроизводима из чистого клона; путь к официальной схеме задаётся аргументом или
  `$OFFICIAL_SCHEMA`.
- [x] Единая команда `tools/check_spec.py`: валидация § 7 + три компаратора + реестр зарегистрированных отклонений
  (`REGISTERED` внутри файла); делит найденное на зарегистрированное и новое, помечает устаревшие записи, `--verbose`
  печатает все ключи, код возврата `1`/`2` — новое/сбой валидации.
- [x] `types_diff.py`: классификация шума по семействам (`alias`, `format_uri`, `null_form`, `payload_relocation`);
  расхождением считается только семейство `real` (`ref:`↔`ref:` двух разных схем).
- [x] Зарегистрировано в `AGENTS.md` § 2.1 расхождение `CommentMessage` в событиях комментариев (оставлен наш тип;
  доказательство — `use-cases/comment-moderation`); строка добавлена и в таблицу «Настоящие расхождения» § 7.1.
- [x] Занесены в `AGENTS.md` § 5 два бага страницы «Модерация комментариев»: `comment_deleted` вместо
  `comment_removed`, `read_all_message` вместо `read_all_messages`.
- [x] Сверка стала обязательным шагом регламента: § 6 п. 4 и § 6.2 (`python3 tools/check_spec.py`), § 7 — вводная строка
  о единой команде, § 7.1 — пути `tools/`, § 2 — строка `tools/` и уточнение `$ref` (473 = 454 + 19).
- [x] Синхронизированы `DOCS_MAP.md` (§ 1, § 7.1, § 7.2), `README.md` (состав, команды, «Последнее обновление»),
  `MAX_API_REFERENCE.md` (тип `message` у событий комментариев); в `.gitignore` — `__pycache__/`, `*.pyc`.
- [x] Журнал: `.agents/journals/sessions/2026-10-20-tools-comparators.md` + строка в `JOURNAL.md`.
- Цифры последнего прогона: валидация `OK`, `$ref` 473 (454 схемы/ответы + 19 параметры) битых нет, дублей ключей нет,
  `OpenAPI 3.1.0 валидна`; сверка — итог **103 зарегистрированных отклонения, новых 0** (код возврата `0`).

---

## Открытые вопросы

1. `POST /chats/{chatId}/members` — снятие/отмена удаления (этап 3). **Статус 2026-10-19: закрыто** — пометка об
   удалении из доки исчезла, операция возвращена в спеку (решение пользователя). Осталось отслеживать, не появится ли
   новая пометка в `changelog-api`.
