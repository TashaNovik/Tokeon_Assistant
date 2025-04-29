from fastapi import APIRouter, Request, HTTPException
from telegram import Update
from telegram.ext import Application

router = APIRouter()

@router.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request) -> dict:
    bot: Application = request.app.state.bot

    if token != bot.token:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook token")

    payload = await request.json()
    update = Update.de_json(payload, bot.bot)
    await bot.update_queue.put(update)

    return {"status": "accepted"}
