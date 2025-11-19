FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/reporting_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/reporting_service /app

EXPOSE 8200

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]

