# app/config.py
#
import os
from pathlib import Path
from dotenv import load_dotenv

# ----------------------------
# MODULE: Environment Configuration
# DESCRIPTION:
#  - Загружает переменные окружения из .env
#  - Предоставляет токен для Telegram-бота
# ----------------------------

# Определяем путь к файлу .env в корне проекта
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)  # Загружаем переменные

# Получаем токен из окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
print(f"Токен из .env: {TELEGRAM_TOKEN}")  # логируем для проверки

# RESPONSIBILITY: прерываем запуск, если токен не задан
if not TELEGRAM_TOKEN:
    raise ValueError("Токен не найден в .env!")
