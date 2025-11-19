## Интеграция с Google Sheets

Бот работает с двумя вкладками одного Spreadsheet:

- `Categories` — иерархия склад → категория → подкатегория (используется `categories_service`).
- `Reports` — отчет по заявкам (`reporting_service` пишет строки).

Минимальный набор переменных окружения (см. `.env.example`):

```
GOOGLE_SHEET_ID=<id таблицы>
GOOGLE_CATEGORIES_SHEET=Categories
GOOGLE_REPORTING_SHEET=Reports
# один из вариантов авторизации. Используйте только один:
GOOGLE_SERVICE_ACCOUNT_FILE=/run/secrets/google.json
GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "..."}'
```

Эти переменные считываются сервисами напрямую, а также представлены в `config/google_sheets.py` для общих настроек.
