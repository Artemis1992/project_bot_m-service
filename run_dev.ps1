param(
    [switch]$RunTests,
    [switch]$RunBot
)

# Корень проекта
$PROJECT_ROOT = "D:\PROJECT_BOT_SERVISE"
Set-Location $PROJECT_ROOT

Write-Host "==> Устанавливаем переменные окружения для dev/test..." -ForegroundColor Cyan

$env:SERVICE_API_KEY            = "test-api-key-12345"
$env:BOT_TOKEN                  = "test-bot-token-12345"   # сюда поставь реальный токен для бота
$env:GOOGLE_SHEET_ID            = "test-sheet-id-12345"
$env:GOOGLE_SERVICE_ACCOUNT_JSON = "{}"
$env:DJANGO_SECRET_KEY          = "test-secret-key"
$env:DJANGO_DEBUG               = "true"

if ($RunTests) {
    Write-Host "==> Запускаем тесты..." -ForegroundColor Yellow

    # Установить зависимости для тестов (один раз)
    pip install -r "$PROJECT_ROOT\tests\requirements.txt"

    # --- requests_service ---
    Write-Host "-> tests for requests_service"
    Set-Location "$PROJECT_ROOT\services\Requests_service"
    python manage.py migrate
    $env:DJANGO_SETTINGS_MODULE = "service_requests.settings"
    pytest "$PROJECT_ROOT\tests\Requests_service" -v

    # --- approvals_service ---
    Write-Host "-> tests for approvals_service"
    Set-Location "$PROJECT_ROOT\services\approvals_service"
    python manage.py migrate
    $env:DJANGO_SETTINGS_MODULE = "approvals_service.settings"
    pytest "$PROJECT_ROOT\tests\approvals_service" -v

    # --- categories_service ---
    Write-Host "-> tests for categories_service"
    Set-Location "$PROJECT_ROOT\services\categories_service"
    python manage.py migrate
    $env:DJANGO_SETTINGS_MODULE = "categories_service.settings"
    pytest "$PROJECT_ROOT\tests\categories_service" -v

    # --- files_service ---
    Write-Host "-> tests for files_service"
    Set-Location "$PROJECT_ROOT\services\files_service"
    pytest "$PROJECT_ROOT\tests\files_service" -v

    # --- reporting_service ---
    Write-Host "-> tests for reporting_service"
    Set-Location "$PROJECT_ROOT\services\reporting_service"
    pytest "$PROJECT_ROOT\tests\reporting_service" -v

    # --- bot_gateway ---
    Write-Host "-> tests for bot_gateway"
    Set-Location "$PROJECT_ROOT\services\bot_gateway"
    pytest "$PROJECT_ROOT\tests\bot_gateway" -v

    Set-Location $PROJECT_ROOT
}

if ($RunBot) {
    Write-Host "==> Запускаем бота..." -ForegroundColor Green
    Set-Location "$PROJECT_ROOT\services\bot_gateway"
    python bot.py
}

if (-not $RunTests -and -not $RunBot) {
    Write-Host "Скрипт ничего не запустил. Используй ключи:" -ForegroundColor Yellow
    Write-Host "  .\run_dev.ps1 -RunTests      # только тесты"
    Write-Host "  .\run_dev.ps1 -RunBot        # только бот"
    Write-Host "  .\run_dev.ps1 -RunTests -RunBot  # сначала тесты, потом бот"
}