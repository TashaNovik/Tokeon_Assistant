# Тесты для Tokeon Assistant

## Структура тестов

### Telegram Bot
- `telegram_bot/` - тесты для модуля Telegram бота
  - `test_handlers.py` - тесты для обработчиков команд и сообщений Telegram
  - `test_main.py` - тесты для основного модуля и создания приложения FastAPI
  - `test_webhook_router.py` - тесты для API роутера webhook
  - `test_config.py` - тесты для конфигурационного модуля
  - `test_integration.py` - интеграционные тесты, охватывающие несколько компонентов
  - `conftest.py` - общие фикстуры для тестов Telegram бота

### Knowledge Base API
- `knowledge_base_api/` - тесты для модуля управления базой знаний
  - `test_main.py` - тесты для основного модуля FastAPI
  - `test_config.py` - тесты для конфигурационного модуля
  - `test_api_router.py` - тесты для API роутера knowledge_base
  - `test_renew_base.py` - тесты для модуля обновления базы знаний
  - `test_chunking.py` - тесты для модуля создания чанков текста
  - `test_qdrant_sender.py` - тесты для модуля взаимодействия с Qdrant
  - `test_integration.py` - интеграционные тесты API для управления базой знаний
  - `conftest.py` - общие фикстуры для тестов Knowledge Base API

## Запуск тестов

### Подготовка

Установите зависимости для тестирования:

```bash
pip install -r tests/requirements-dev.txt
```

### Запуск всех тестов

```bash
pytest
```

### Запуск только тестов Telegram Bot

```bash
pytest tests/telegram_bot/
```

### Запуск только тестов Knowledge Base API

```bash
pytest tests/knowledge_base_api/
```

### Запуск только модульных тестов

```bash
pytest -m unit
```

### Запуск только интеграционных тестов

```bash
pytest -m integration
```

### Запуск тестов с отчетом о покрытии

```bash
# Для всех модулей
pytest --cov=telegram_bot --cov=knowledge_base_api tests/

# Для конкретного модуля
pytest --cov=knowledge_base_api tests/knowledge_base_api/
```

## Добавление новых тестов

1. Создайте новый файл в соответствующей директории
2. Имя файла должно начинаться с `test_`
3. Имена функций тестов должны начинаться с `test_`
4. Используйте существующие фикстуры из `conftest.py`
5. При необходимости добавьте новые маркеры в `pytest.ini` 