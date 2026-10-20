---
tags: [ openapi, schema, update, comparators, validation, fix, docs ]
date: 2026-10-20
---

## Проблема

Две задачи, обе — следствие разбора отличия № 2 (`Update`):

1. **Дублирование в `Update`.** Общие поля события (`update_type`, `timestamp` и их обязательность) были записаны
   дважды — и в `UpdateBase`, и инлайн в `Update`. Состав и `required` совпадали полностью, то есть это была чистая
   копия, которую нужно было вынести в `allOf: [$ref: UpdateBase]`.
2. **Сброс окружения.** Каталог `/tmp/opencode` оказался пуст: исчезли `max-official/schema.yaml`, компараторы
   `diff_official.py` / `types_diff.py` и venv `openapi-spec-validator`. Их нужно было пересоздать по регламенту
   `AGENTS.md` § 7 / § 7.1, прежде чем что-либо сверять.

## Решение

**`Update` без дублирования.** В `openapi.yaml` из схемы `Update` удалены `properties` и `required`, вместо них добавлен
`allOf: [$ref: "#/components/schemas/UpdateBase"]`; `discriminator` и `oneOf` из 19 подтипов не тронуты, описание
дополнено пояснением, что общие поля и их обязательность берутся из `UpdateBase`. Циклов нет: подтипы ссылаются на
`UpdateBase`, а на сам `Update` не ссылается никто — он точка входа в `paths`.

**Окружение пересоздано:**

- `git clone --depth 1 https://github.com/max-messenger/api-schema.git /tmp/opencode/max-official` — официальная схема
  не менялась: коммит `1a4a502`, v0.0.33, 2026-09-18;
- заново написаны компараторы (прежний код жил вне репозитория и не сохраняется): `/tmp/opencode/diff_official.py`
  (пути, операции, имена схем, поля и `required` с разворачиванием `allOf`/`$ref` с обеих сторон,
  `components/parameters`,
  `components/responses`, битые ссылки) и `/tmp/opencode/types_diff.py` (типы/nullability/enum; nullability читается и
  как `type: [x, "null"]`/`anyOf` с `null`, и как официальный `nullable: true`, поэтому обе формы сравнимы); выводы —
  `/tmp/opencode/diff_2026-10-20.txt`, `/tmp/opencode/types_2026-10-20.txt`;
- venv пересоздан: `python3 -m venv /tmp/opencode/.venv-oas` + `pip install openapi-spec-validator`.

**Документы.** `AGENTS.md`: в § 2.1 строка про имена подтипов `Update` дополнена наследованием через `allOf` (и датой
2026-10-20); в § 7.1 добавлен блок «Подтверждено 2026-10-20» с цифрами пересозданных компараторов, исправлена ссылка на
источник строк `тип:` (`types_diff.py`, а не `diff_official.py`), уточнено, что `Update` в diff не появляется именно
из-за наследования полей из `UpdateBase`, и что сознательных отклонений по nullability **два**, а не одно:
`Message.body` (§ 2.1) и `UserRemovedFromChatUpdate.admin_id` (§ 5). `MAX_API_REFERENCE.md` править не потребовалось —
`UpdateBase` и внутренняя структура объединения там не описываются.

## Проверка

Все четыре команды `AGENTS.md` § 7 прогнаны 2026-10-20, цифры из последнего прогона:

- YAML-синтаксис → `OK`;
- разрешение `$ref` → `Все 454 ссылок резолвятся`, 0 broken;
- дубли ключей YAML → `дублей ключей нет`;
- `openapi-spec-validator` → `OpenAPI 3.1.0 валидна`.

Поведенческая проверка схемы `Update` новым компаратором/валидатором JSON Schema (jsonschema 2020-12 из venv,
`$ref` разрешены через `referencing`): объект без `timestamp` отклонён с `'timestamp' is a required property`
(то есть `required` из `UpdateBase` доезжает через `allOf`), `bot_added` без `chat_id`/`user`/`is_channel` отклонён,
`message_callback` без `callback` отклонён, событие с неизвестным `update_type` отклонено (закрытый `enum`), полностью
корректный `bot_added` принят. Поведение до и после дедупликации не изменилось.

Машинная сверка после правки: пути 18 = 18, операции **33 = 33**, схем официально 133 / у нас 106 (нет у нас **41**,
лишних **14**), битых ссылок нет. `types_diff.py`: nullability-расхождений **2** — `UserRemovedFromChatUpdate.admin_id`
и `Message.body`, оба зарегистрированы (§ 5 / § 2.1); enum-расхождений **0** (две строки — только порядок значений
`Chat.type` и `Recipient.chat_type`).

## Нюансы

- Пересозданный `types_diff.py` показывает строку `Message.body` (у нас обязательное, но nullable; официально —
  обязательное, не nullable), которой в прошлом выводе не было. Расхождение не новое: оно давно зарегистрировано в §
  2.1, просто прежняя версия скрипта его не выводила. Формулировку § 7.1 про «единственное отклонение» пришлось
  исправить на два.
- Строки `тип: офиц[any]/офиц[null] vs у нас[...]` — по-прежнему шум разворачивания `allOf`; реальные расхождения только
  в итоговых блоках `NULLABILITY`/`ENUM` и строке «Итого».
- Компараторы и клон официальной схемы снова живут только в `/tmp/opencode` — при следующем сбросе окружения их придётся
  пересоздать; регламент и ожидаемые цифры зафиксированы в § 7.1.
- Коммит не делался (`AGENTS.md` § 6.2).
