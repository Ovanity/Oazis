FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir \
    "aiogram>=3.22.0" \
    "apscheduler>=3.11.1" \
    "loguru>=0.7.3" \
    "pydantic>=2.11.10" \
    "pydantic-settings>=2.6.1" \
    "sqlmodel>=0.0.27"

COPY . .

RUN mkdir -p data

CMD ["python", "main.py"]

