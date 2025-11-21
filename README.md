## О проекте

Это набор микросервисов для Telegram‑бота, который помогает оформлять служебки/заявки:

- пользователь в Telegram заполняет заявку по шагам с кнопками;
- бот складывает данные в `requests_service`;
- запускается цепочка согласований в `approvals_service`;
- файлы улетают в хранилище через `files_service`;
- отчёты пишутся в Google Sheets через `reporting_service`;
- дерево категорий и складов берётся из Google Sheets через `categories_service`.

Проект можно использовать как готовый шаблон, а можно доработать под свой бизнес‑процесс.

## Технологии

- **Язык**: Python 3.11+
- **Telegram‑бот**: Aiogram 3 (`bot_gateway`)
- **Web / API**:
  - Django 5.1 + Django REST Framework (`requests_service`, `approvals_service`, `categories_service`)
  - FastAPI (`files_service`, `reporting_service`)
- **Хранилища и интеграции**:
  - Postgres 16 (основная БД для Django‑сервисов)
  - Google Sheets (категории, отчётность)
  - Google Drive / S3 (хранение файлов)
- **Инфраструктура**:
  - Docker / docker‑compose
  - `pytest` + отдельные `tests/requirements.txt` для тестов

## Архитектура

Логика разбита на несколько сервисов, каждый отвечает за свой кусок:

- **`bot_gateway`** — Telegram‑бот:
  - FSM‑диалог с пользователем;
  - главное меню (создать заявку, мои заявки, помощь);
  - обращается к остальным сервисам только по HTTP.

- **`requests_service`** (Django + DRF):
  - модель заявки и вложений;
  - создание/чтение/частичное редактирование заявок;
  - вызов `approvals_service` и `reporting_service` при создании;
  - хранит статус заявки и текущий уровень согласования.

- **`approvals_service`** (Django + DRF):
  - цепочки согласований, шаги, статусы;
  - двигает заявку по маршруту (Денис → Жасулан → Мейржан → Лязат/Айгуль);
  - синхронизирует статус обратно в `requests_service`;
  - через `bot_gateway` шлёт уведомления согласующим и автору.

- **`categories_service`** (Django + DRF + gspread):
  - дерево склад → категория → подкатегория;
  - умеет синхронизировать дерево из Google Sheets;
  - отдаёт структуру в бота для построения кнопок.

- **`files_service`** (FastAPI):
  - принимает file_id из Telegram;
  - скачивает файл, сохраняет в Drive/S3;
  - возвращает ссылку и путь для привязки к заявке.

- **`reporting_service`** (FastAPI + gspread):
  - пишет заявки в отчётный лист Google Sheets;
  - используется `requests_service` через клиент.

Общение между сервисами идёт по HTTP, защищено общим `SERVICE_API_KEY`.

## Структура директорий

Самое важное:

- `services/`
  - `bot_gateway/` — код Telegram‑бота:
    - `bot.py` — точка входа;
    - `api/` — HTTP‑клиенты к другим сервисам;
    - `fsm/` — состояния, хендлеры, клавиатуры.
  - `requests_service/` — Django‑сервис заявок.
  - `approvals_service/` — Django‑сервис согласований.
  - `categories_service/` — Django‑сервис категорий.
  - `files_service/` — FastAPI‑сервис файлов.
  - `reporting_service/` — FastAPI‑сервис отчётности.
- `docker/`
  - `docker-compose.yml` — общий запуск всего стека;
  - `*-service.Dockerfile` — образы сервисов.
- `config/`
  - общая конфигурация Google Sheets.
- `tests/`
  - набор автотестов по всем сервисам + интеграционные тесты.
- `env.example`
  - пример файла окружения со всеми переменными.

## Как запустить локально

### Вариант 1 — через Docker (рекомендуется)

1. **Скопируйте и заполните `.env`:**

```bash
cp env.example .env        # Linux / Mac
Copy-Item env.example .env # Windows PowerShell
```

Минимально нужно задать:

- `BOT_TOKEN` — токен Telegram‑бота от @BotFather;
- `SERVICE_API_KEY` — любой строковый ключ, одинаковый для всех сервисов.

Google‑переменные (`GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`) можно оставить пустыми, если отчёты и синхронизация с таблицами пока не нужны.

2. **Поднимите весь стек:**

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

3. **Примените миграции для Django‑сервисов:**

```bash
docker compose -f docker/docker-compose.yml exec requests_service python manage.py migrate
docker compose -f docker/docker-compose.yml exec categories_service python manage.py migrate
docker compose -f docker/docker-compose.yml exec approvals_service python manage.py migrate
```

4. **Проверьте, что сервисы поднялись:**

```bash
curl http://localhost:8000/api          # requests_service
curl http://localhost:8001/api          # categories_service
curl http://localhost:8002/api          # approvals_service
curl http://localhost:8100/health       # files_service
curl http://localhost:8200/health       # reporting_service
```

5. **Запустите бота (если он не стартует из Docker):**

```bash
cd services/bot_gateway
python bot.py
```

После этого можно писать боту в Telegram и проходить сценарий создания заявки.

### Вариант 2 — без Docker (для отладки)

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости нужного сервиса:

```bash
pip install -r services/requests_service/requirements.txt
```

3. Пропишите переменные окружения (можно взять из `env.example`).
4. Для Django‑сервисов:

```bash
cd services/requests_service
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

5. Для FastAPI‑сервисов:

```bash
cd services/files_service
uvicorn main:app --reload --host 0.0.0.0 --port 8100
```

Бот в этом случае всё равно общается с сервисами по HTTP, только по `localhost`.

## Как запускать тесты

1. **Установить зависимости для тестов:**

```bash
pip install -r tests/requirements.txt
```

2. **Минимальные переменные окружения** (можно тестовые):

```bash
export SERVICE_API_KEY="test-api-key-12345"
export BOT_TOKEN="test-bot-token-12345"
export GOOGLE_SHEET_ID="test-sheet-id-12345"
export GOOGLE_SERVICE_ACCOUNT_JSON="{}"
export DJANGO_SECRET_KEY="test-secret-key"
```

3. **Запуск всех тестов из корня:**

```bash
pytest tests -v
```

4. **Запуск тестов конкретного сервиса**, пример для `requests_service`:

```bash
cd services/requests_service
DJANGO_SETTINGS_MODULE=service_requests.settings pytest ../../tests/requests_service -v
```

В `tests/README.md` описаны все группы тестов и дополнительные сценарии (интеграционные, с реальными Google‑сервисами и т.п.).

## План перехода в микросервисы

Фактически проект уже разбит на микросервисы, но есть, что улучшать, чтобы чувствовать себя как в "настоящей" продакшен‑микросервисной архитектуре.

- **1. Жёстко оторваться от общего кода**
  - Сейчас сервисы всё ещё живут в одном репозитории.
  - Возможный следующий шаг — вынести их в отдельные репозитории или хотя бы в отдельные Docker‑образы с независимыми релизами.

- **2. Выделить общие вещи в библиотеки**
  - Клиенты (`SERVICE_API_KEY`‑аутентификация, retry‑логика);
  - схемы запросов/ответов (pydantic‑модели) для унификации контрактов;
  - общее логирование и трейсинг.

- **3. Добавить шину событий**
  - Сейчас связь в основном синхронная по HTTP.
  - Можно добавить брокер (RabbitMQ / Kafka / Redis Streams) и перевести часть сценариев в асинхронные события:
    - "заявка создана",
    - "заявка утверждена/отклонена",
    - "файл загружен",
    - "строка записана в отчёт".

- **4. Усилить наблюдаемость**
  - Централизованные логи (ELK/Graylog);
  - метрики и алерты (Prometheus + Grafana);
  - request‑ID/trace‑ID между сервисами.

- **5. Отдельный сервис уведомлений**
  - Сейчас уведомления проходят через `bot_gateway` + `NotificationService`.
  - Можно выделить `notifications_service`, который будет отвечать за Telegram, e‑mail, чаты и т.п.

- **6. Продакшен‑обвязка**
  - Ingress / reverse‑proxy (nginx/traefik) перед сервисами;
  - отдельные базы/кластеры для разных сервисов;
  - CI/CD пайплайны на каждый сервис.

Проект уже можно запускать как микросервисный, но все пункты выше — это дорожная карта, как постепенно довести его до "боевого" уровня.
