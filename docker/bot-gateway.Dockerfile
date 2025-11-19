FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/bot_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/bot_gateway /app

CMD ["python", "bot.py"]


