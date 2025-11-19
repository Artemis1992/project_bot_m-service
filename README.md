# PROJECT_BOT_SERVICE

Готовый набор микросервисов для Telegram-бота: сбор заявок, согласование, загрузка вложений в Drive, отчетность в Google Sheets и выдача дерева категорий.

## Что внутри
- `bot_gateway` (Aiogram): диалоги бота, обращается к API других сервисов.
- `requests_service` (Django + DRF): CRUD заявок + вложения.
- `approvals_service` (Django + DRF): цепочки согласований.
- `categories_service` (Django + DRF + gspread): дерево склад → категория → подкатегория, синхронизация с Google Sheets.
- `files_service` (FastAPI): скачивание файлов из Telegram и загрузка в Google Drive (есть S3-модуль).
- `reporting_service` (FastAPI + gspread): запись заявок в отчетный лист Google Sheets.
- Инфраструктура: Postgres, docker-compose, общая конфигурация Google Sheets (`config/`).

Стек: Python 3.11+, Django 5.1, DRF, FastAPI, Aiogram 3, Postgres 16, gspread.

## Быстрый старт (Docker)
1. Скопируйте переменные: `cp .env.example .env` и заполните токены/ID таблицы. Обязательно задайте `BOT_TOKEN`, `GOOGLE_*` и секреты БД.
2. Соберите и поднимите: `docker compose -f docker/docker-compose.yml up -d --build`.
3. Примените миграции для Django-сервисов:
   - `docker compose -f docker/docker-compose.yml exec requests_service python manage.py migrate`
   - `docker compose -f docker/docker-compose.yml exec categories_service python manage.py migrate`
   - `docker compose -f docker/docker-compose.yml exec approvals_service python manage.py migrate`
4. Проверить готовность: `curl http://localhost:8000/api` (requests), `:8001/api` (categories), `:8002/api`, `:8100/health`, `:8200/health`.

## Основные переменные окружения
- `BOT_TOKEN` — токен Telegram-бота.
- `DATABASE_URL` — строка подключения Postgres (см. .env.example).
- `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DEBUG` — базовые настройки Django.
- `GOOGLE_SHEET_ID`, `GOOGLE_CATEGORIES_SHEET=Categories`, `GOOGLE_REPORTING_SHEET=Reports`.
- `GOOGLE_SERVICE_ACCOUNT_FILE` **или** `GOOGLE_SERVICE_ACCOUNT_JSON` — учетные данные для Sheets/Drive.
- URL-ы сервисов (для локального запуска без Docker): `CATEGORIES_SERVICE_URL`, `REQUESTS_SERVICE_URL`, `APPROVALS_SERVICE_URL`, `FILES_SERVICE_URL`, `REPORTING_SERVICE_URL`.

Полный список и дефолты — в `.env.example`.

## Порты и точки входа
- `requests_service` — `:8000` (`/api/requests/...`)
- `categories_service` — `:8001` (`/api/categories/...`)
- `approvals_service` — `:8002` (`/api/approvals/...`)
- `files_service` — `:8100` (`/health`, `/files/from-telegram`)
- `reporting_service` — `:8200` (`/health`, `/reports/requests`)
- `bot_gateway` — телеграм-бот, запускается из `services/bot_gateway/bot.py`.

## Запуск без Docker (для отладки)
- Активируйте venv, установите зависимости конкретного сервиса (`pip install -r services/<service>/requirements.txt`).
- Пропишите переменные окружения из `.env.example`.
- Django: `python manage.py migrate && python manage.py runserver 0.0.0.0:8000` (подставьте порт сервиса).
- FastAPI: `uvicorn main:app --reload --host 0.0.0.0 --port 8100`.

## Подготовка к продакшену
- Выставить `DJANGO_DEBUG=false`, настоящие `DJANGO_SECRET_KEY` и закрытые `ALLOWED_HOSTS`.
- Убедиться, что `DATABASE_URL` указывает на внешнюю БД; настроить бэкапы Postgres.
- Настроить учетные данные Google (secrets/volumes) и реальные имена листов `Categories` и `Reports`.
- Прописать `CSRF_TRUSTED_ORIGINS` для Django-сервисов, если будут веб-хуки/панели.
- Включить централизованный сбор логов и мониторинг; добавить reverse-proxy (nginx/traefik) с TLS.
- Прогнать миграции перед запуском каждой новой версии.
- Настроить брандмауэр/ACL для сервисов файлов и отчетов, так как авторизации пока нет.

## Дальнейшие шаги
- Добавить авторизацию/аутентификацию для всех API.
- Покрыть интеграции (Sheets/Drive/S3/Telegram) автотестами.
- Связать approvals → reporting → requests событиями/вебхуками по нужному бизнес-потоку.
