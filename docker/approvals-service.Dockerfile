FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/approvals_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/approvals_service /app

EXPOSE 8002

CMD ["gunicorn", "approvals_service.wsgi:application", "--bind", "0.0.0.0:8002"]

