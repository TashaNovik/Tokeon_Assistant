from fastapi import APIRouter, Request, HTTPException
from telegram import Update
from telegram.ext import Application

router = APIRouter()

@router.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request) -> dict:
    """
    Receive webhook updates from Telegram.
    1) Validate the webhook token in the URL.
    2) Parse incoming JSON into a Telegram Update.
    3) Enqueue the update for the polling bot.
    """
    bot: Application = request.app.state.bot

    if token != bot.token:
        # Reject requests with invalid tokens
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook token")

    payload = await request.json()
    update = Update.de_json(payload, bot.bot)
    await bot.update_queue.put(update)

    return {"status": "accepted"}
