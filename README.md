# MAX Messenger API — спецификация OpenAPI

Спецификация OpenAPI 3.1.0 для Bot API мессенджера [MAX](https://max.ru), сгенерированная по официальной документации
на [dev.max.ru/docs-api](https://dev.max.ru/docs-api).

## Описание API

Блок `info.description` из спецификации:

API MAX — это интерфейс, который позволяет ботам взаимодействовать с платформой MAX и получать необходимые данные с
помощью HTTPS-запросов к серверу.

**Важно:**

- Используйте домен `platform-api2.max.ru` вместо `platform-api.max.ru`.
- Добавьте сертификат Минцифры в список доверенных.
- HTTP вебхуки больше не поддерживаются — используйте HTTPS.
- Long Polling ограничен по скорости и сроку хранения событий — не подходит для production.
- Лимит запросов: 30 RPS на `platform-api2.max.ru`.

## Ключевые факты

| Факт                     | Значение                                                                                                                                                                           |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Base URL**             | `https://platform-api2.max.ru`                                                                                                                                                     |
| **Авторизация**          | заголовок `Authorization: <access_token>` (передача токена через query-параметры больше не поддерживается)                                                                         |
| **Версия спецификации**  | OpenAPI 3.1.0                                                                                                                                                                      |
| **Лимит запросов**       | 30 RPS на `platform-api2.max.ru`                                                                                                                                                   |
| **Последнее обновление** | 2026-09-27 (сверка с `dev.max.ru/docs-api/changelog-api`, текстовыми страницами доков и официальной спекой `max-messenger/api-schema` v0.0.33; неподтверждённых полей не осталось) |

## Содержимое

| Файл                   | Описание                                                                                                                                                                             |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `openapi.yaml`         | Полная спецификация OpenAPI 3.1.0 — 18 путей, 32 метода, 105 схем, все ссылки `$ref` проверены                                                                                       |
| `MAX_API_REFERENCE.md` | Человекочитаемый справочник API с примерами, правилами раскладки клавиатуры, таблицами форматирования текста, правилами комбинирования вложений и схемой верификации request_contact |
| `DOCS_MAP.md`          | Карта официальной документации: разделы, все 32 метода с URL, объекты, регламент отслеживания релизов                                                                                |
| `AGENTS.md`            | Правила работы, ключевые факты, сознательные отклонения от официальной схемы, реестр полей и регламент сверки                                                                        |

## Покрытие

- **32 метода API** — Боты (2), Чаты (13), Подписки и Long Polling (4), Загрузки (1), Сообщения и ответы (7),
  Комментарии (5)
- **Объекты** — User, UserWithPhoto, BotInfo, ChatMember, Chat, Message, MessageBody, LinkedMessage, NewMessageLink,
  NewMessageBody, CommentMessage, NewCommentBody, Update, MarkupElement
- **19 типов событий** — 19 подтипов `Update` с `discriminator` по `update_type`, включая `comment_created` /
  `comment_edited` / `comment_removed` (добавлены в августе 2026) и `bot_admin_permissions_changed` (только в
  официальной `schema.yaml`)
- **Система клавиатуры/кнопок** — 7 типов кнопок, схема inline-клавиатуры (210 кнопок / 30 рядов / 7 в ряду)
- **Типы вложений** — image, video, audio, file, sticker, inline_keyboard, location, share
- **Форматирование текста** — таблицы синтаксиса Markdown и HTML + разобранная разметка в ответе (`markup`)
- **Загрузка медиафайлов** — домены загрузки, resumable и multipart, работа с токенами
- **Коды ошибок** — 200, 400, 401, 404, 405, 429, 503 на всех эндпоинтах

## Сверка с официальной документацией

Проект сверяется с двумя источниками (см. `AGENTS.md` §3 и `DOCS_MAP.md` §7):

```bash
# 1. Журнал релизов API — первое, что проверять
#    https://dev.max.ru/docs-api/changelog-api

# 2. Официальная машинная спека — источник правды по типам и полям
git clone --depth 1 https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official
python3 /tmp/opencode/diff_official.py openapi.yaml
```

## Проверка

```bash
# Проверка синтаксиса YAML
python3 -c "import yaml; yaml.safe_load(open('openapi.yaml')); print('OK')"

# Проверка разрешения $ref
python3 -c "
import yaml, re
spec = yaml.safe_load(open('openapi.yaml'))
schemas = set(spec['components']['schemas'].keys())
responses = set(spec['components']['responses'].keys())
refs = re.findall(r'\"#/components/(schemas|responses)/(\w+)\"', open('openapi.yaml').read())
broken = [f'{t}/{n}' for t, n in refs if n not in (schemas if t == 'schemas' else responses)]
print(f'{len(refs)} refs, {len(broken)} broken' if broken else f'Все {len(refs)} ссылок резолвятся')
"
```

## Сертификат Минцифры (Russian Trusted Root CA)

API MAX обслуживается на домене `platform-api2.max.ru`, защищённом TLS-сертификатом, выпущенным национальным
удостоверяющим центром Минцифры России (НУЦ). Чтобы HTTPS-запросы к API проходили без ошибки верификации сертификата,
нужно добавить корневой и выпускающий сертификаты НУЦ в список доверенных.

### Где взять сертификаты

Скачивайте сертификаты только с официальных ресурсов Минцифры / Госуслуг:

- Официальная страница с инструкциями и ссылками: <https://www.gosuslugi.ru/crt>
- Корневой сертификат **Russian Trusted Root CA**
  (PEM): <https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt>
- Выпускающий (промежуточный) сертификат **Russian Trusted Sub CA**
  (PEM): <https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt>
- Альтернативный каталог файлов (CER, iOS, macOS): <https://gu-st.ru/content/Other/doc/>

### Установка в доверенные на Debian/Ubuntu

Debian использует хранилище `/usr/local/share/ca-certificates/` и команду `update-ca-certificates`. Сертификаты должны
быть в формате PEM с расширением `.crt`.

```bash
# 1. Скачать сертификаты
wget https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt
wget https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt

# 2. Скопировать в хранилище доверенных сертификатов
sudo cp russian_trusted_root_ca_pem.crt /usr/local/share/ca-certificates/russian_trusted_root_ca.crt
sudo cp russian_trusted_sub_ca_pem.crt /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt

# 3. Обновить хранилище
sudo update-ca-certificates

# 4. Проверить, что сертификаты в списке доверенных
awk '/russian_trusted/{print}' /etc/ssl/certs/ca-certificates.crt | head -1
```

Проверка соединения с API после установки:

```bash
curl -v https://platform-api2.max.ru 2>&1 | grep "SSL certificate verify"
```

> Примечание: если клиент использует собственное хранилище (например, Node.js с настройкой
> `NODE_EXTRA_CA_CERTS`, Python с параметром `verify=`, curl с `--cacert`), сертификаты нужно
> добавить в хранилище именно этого клиента — системное хранилище Debian покрывает только
> приложения, которые читают `/etc/ssl/certs/ca-certificates.crt`.

## Лицензия

Проект распространяется по лицензии **MIT** — см. файл [LICENSE](LICENSE).

Сам API MAX и его документация являются проприетарными, поэтому данная спецификация — неофициальная, составленная по
публично доступным материалам.
