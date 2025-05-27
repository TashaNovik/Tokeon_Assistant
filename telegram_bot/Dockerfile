FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY ./telegram_bot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./telegram_bot /app/telegram_bot

EXPOSE 8000

CMD ["uvicorn", "telegram_bot.main:app", "--host", "0.0.0.0", "--port", "8000"]
