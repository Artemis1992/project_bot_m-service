# 🚀 Быстрый запуск бота (5 минут)

## Минимальные требования

1. **BOT_TOKEN** - токен от @BotFather (обязательно, реальный)
2. **SERVICE_API_KEY** - любой строковый ключ
3. **Все сервисы запущены**

---

## Шаг 1: Получите BOT_TOKEN (5 минут)

1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/BotFather)
3. Отправьте `/newbot`
4. Следуйте инструкциям
5. Скопируйте токен

**📖 Подробно:** [tests/SETUP_KEYS.md](tests/SETUP_KEYS.md#2-bot_token-telegram)

---

## Шаг 2: Установите переменные (1 минута)

**Windows PowerShell:**
```powershell
$env:BOT_TOKEN="ваш_токен_от_BotFather"
$env:SERVICE_API_KEY="test-api-key-12345"
```

**Linux/Mac:**
```bash
export BOT_TOKEN="ваш_токен_от_BotFather"
export SERVICE_API_KEY="test-api-key-12345"
```

**⚠️ ВАЖНО:** `SERVICE_API_KEY` должен быть **одинаковым** во всех сервисах!

---

## Шаг 3: Запустите через Docker

```bash
# Запустите все сервисы
docker compose -f docker/docker-compose.yml up -d

# Примените миграции
docker compose -f docker/docker-compose.yml exec requests_service python manage.py migrate
docker compose -f docker/docker-compose.yml exec categories_service python manage.py migrate
docker compose -f docker/docker-compose.yml exec approvals_service python manage.py migrate

# Проверьте логи бота
docker compose -f docker/docker-compose.yml logs bot_gateway
```

---

## Шаг 4: Протестируйте

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Бот должен ответить и начать диалог

---

## Или запустите локально

```bash
# 1. Установите зависимости
cd services/bot_gateway
pip install -r requirements.txt

# 2. Убедитесь, что все сервисы запущены на localhost

# 3. Установите переменные (см. выше)

# 4. Запустите бота
python bot.py
```

---

## ❓ Проблемы?

- **"BOT_TOKEN is not set"** → Установите переменную `BOT_TOKEN`
- **"Connection refused"** → Убедитесь, что все сервисы запущены
- **"401 Unauthorized"** → Проверьте, что `SERVICE_API_KEY` одинаковый везде
- **Бот не отвечает** → Проверьте логи и токен

**📖 Полная инструкция:** [BOT_SETUP.md](BOT_SETUP.md)






