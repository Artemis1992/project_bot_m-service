# 🚀 Быстрый старт тестирования

## Минимальная настройка (5 минут)

### Шаг 1: Установите зависимости
```bash
pip install -r tests/requirements.txt
```

### Шаг 2: Установите тестовые переменные окружения

**Windows PowerShell:**
```powershell
$env:SERVICE_API_KEY="test-api-key-12345"
$env:BOT_TOKEN="test-bot-token-12345"
$env:GOOGLE_SHEET_ID="test-sheet-id-12345"
$env:GOOGLE_SERVICE_ACCOUNT_JSON="{}"
$env:DJANGO_SECRET_KEY="test-secret-key"
```

**Linux/Mac:**
```bash
export SERVICE_API_KEY="test-api-key-12345"
export BOT_TOKEN="test-bot-token-12345"
export GOOGLE_SHEET_ID="test-sheet-id-12345"
export GOOGLE_SERVICE_ACCOUNT_JSON="{}"
export DJANGO_SECRET_KEY="test-secret-key"
```

### Шаг 3: Прогоняем миграции Django (один раз)

Для корректной работы тестов Django‑сервисов нужно один раз создать таблицы в БД.

**Windows PowerShell (рекомендуемый путь):**

```powershell
cd D:\PROJECT_BOT_SERVISE

# approvals_service
cd services\approvals_service
python manage.py makemigrations approvals_app
python manage.py migrate

# categories_service
cd ..\categories_service
python manage.py makemigrations categories_app
python manage.py migrate

cd D:\PROJECT_BOT_SERVISE
```

Если запускаете на Linux/Mac, команды те же, только с прямыми слешами и без `D:\`.

### Шаг 4: Запускаем все тесты через скрипт (Windows PowerShell)

В корне проекта есть скрипт `run_dev.ps1`, который прогоняет тесты по всем сервисам:

```powershell
cd D:\PROJECT_BOT_SERVISE

# активировать виртуальное окружение (если ещё не активировано)
.\venv\Scripts\Activate.ps1

# запустить все тесты
.\run_dev.ps1 -RunTests
```

Скрипт сам:

- выставит тестовые переменные окружения;
- запустит миграции и pytest для `requests_service`, `approvals_service`, `categories_service`;
- прогонит тесты для `files_service`, `reporting_service` и `bot_gateway`.

### Шаг 5: Запуск тестов для конкретного сервиса вручную

Если нужно проверить только один сервис, можно запускать pytest по‑старому:

```powershell
# Пример: только requests_service
cd D:\PROJECT_BOT_SERVISE\services\Requests_service
$env:DJANGO_SETTINGS_MODULE = "service_requests.settings"
pytest ..\..\tests\Requests_service -v

# Пример: только bot_gateway
cd D:\PROJECT_BOT_SERVISE\services\bot_gateway
pytest ..\..\tests\bot_gateway -v
```

## Что дальше?

- **Для тестов с моками:** Вышеуказанных переменных достаточно
- **Для полного тестирования:** Получите реальные ключи (см. [SETUP_KEYS.md](SETUP_KEYS.md))
- **Для продакшена:** Используйте безопасные ключи (см. [SETUP_KEYS.md](SETUP_KEYS.md))





