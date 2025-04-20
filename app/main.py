# app/main.py
#
import asyncio, logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from app.routers.tg_bot import create_bot

# ----------------------------
# MODULE: Application Bootstrap & Lifecycle
# DESCRIPTION:
#  - Инициализация FastAPI и Telegram-бота
#  - Управление startup/shutdown событиями
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("app")

app = FastAPI()
bot: Application = create_bot()

@app.on_event("startup")
async def startup():
    # RESPONSIBILITY: готовим и запускаем Telegram-бота в режиме polling
    logger.info("Запуск Telegram-бота")
    await bot.initialize()             # подготовка внутренних структур
    await bot.start()                  # запускаем диспетчер команд
    await bot.bot.delete_webhook()     # отключаем вебхук (если был)
    asyncio.create_task(bot.updater.start_polling())
    logger.info("Бот запущен (polling)")

@app.on_event("shutdown")
async def shutdown():
    # RESPONSIBILITY: корректно останавливаем polling и очищаем ресурсы
    logger.info("Остановка polling")
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    logger.info("Бот остановлен")

# ----------------------------
# MODULE: HTTP Endpoints for Integrations
# DESCRIPTION:
#  - Health-check, webhook при необходимости
# ----------------------------
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/webhook/{token}")
async def webhook(token: str, req: Request):
    # RESPONSIBILITY: приём апдейтов от Telegram по webhook
    if token != bot.token:
        return {"error": "invalid token"}
    data = await req.json()
    update = Update.de_json(data, bot.bot)
    await bot.update_queue.put(update)
    return {"status": "accepted"}
