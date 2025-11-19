FROM python:3.12-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/requests_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/requests_service /app

EXPOSE 8000

CMD ["gunicorn", "service_requests.wsgi:application", "--bind", "0.0.0.0:8000"]

