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

| Факт                     | Значение                                                                                                   |
|--------------------------|------------------------------------------------------------------------------------------------------------|
| **Base URL**             | `https://platform-api2.max.ru`                                                                             |
| **Авторизация**          | заголовок `Authorization: <access_token>` (передача токена через query-параметры больше не поддерживается) |
| **Версия спецификации**  | OpenAPI 3.1.0                                                                                              |
| **Лимит запросов**       | 30 RPS на `platform-api2.max.ru`                                                                           |
| **Последнее обновление** | 14.08.2026 (верификация против доков 2026-08-14)                                                           |

## Содержимое

| Файл                   | Описание                                                                                                                                                                             |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `openapi.yaml`         | Полная спецификация OpenAPI 3.1.0 — 17 путей, 43 схемы, все ссылки `$ref` проверены                                                                                                  |
| `MAX_API_REFERENCE.md` | Человекочитаемый справочник API с примерами, правилами раскладки клавиатуры, таблицами форматирования текста, правилами комбинирования вложений и схемой верификации request_contact |

## Покрытие

- **29 методов API** — Боты, Чаты (14), Подписки, Обновления, Загрузки, Сообщения, Ответы
- **8+ типов объектов** — User, UserWithPhoto, BotInfo, ChatMember, Chat, Message, Update, NewMessageBody
- **Система клавиатуры/кнопок** — 7 типов кнопок, схема inline-клавиатуры (210 кнопок / 30 рядов / 7 в ряду)
- **Типы вложений** — image, video, audio, file, sticker, inline_keyboard, location, share
- **Форматирование текста** — таблицы синтаксиса Markdown и HTML
- **Загрузка медиафайлов** — домены загрузки, resumable и multipart, работа с токенами
- **Коды ошибок** — 200, 400, 401, 404, 405, 429, 503 на всех эндпоинтах

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
