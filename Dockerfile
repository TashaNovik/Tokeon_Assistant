# 1. Базовый образ (лёгкий вариант Python 3.9)
FROM python:3.9-slim

# 2. Определяем рабочую директорию внутри контейнера
WORKDIR /usr/src/app

# 3. Копируем файл с зависимостями
COPY requirements.txt .

# 4. Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь проект (исключая то, что прописано в .dockerignore)
COPY . .

# 6. При запуске контейнера выполняем команду - запуск Python
# (Указываем, что у нас в main.py стартует и Telegram-бот, и веб-приложение)
CMD [ "python", "app/main.py" ]
