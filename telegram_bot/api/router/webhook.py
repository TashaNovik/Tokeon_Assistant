from fastapi import APIRouter, Request, HTTPException
from telegram import Update
from telegram.ext import Application

router = APIRouter()

@router.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request) -> dict:
    """
    Receive and process Telegram webhook updates.

    Steps:
    1) Validate the token provided in the webhook URL against the bot token.
    2) Parse the incoming JSON payload into a Telegram Update object.
    3) Enqueue the update into the bot's update queue for asynchronous processing.

    Args:
        token (str): Webhook token from the URL path to validate the request.
        request (Request): FastAPI request object containing the incoming webhook data.

    Raises:
        HTTPException: If the token does not match the bot's token (401 Unauthorized).

    Returns:
        dict: A JSON response confirming the update was accepted.
    """
    bot: Application = request.app.state.bot

    if token != bot.token:
        # Reject requests with invalid tokens
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook token")

    payload = await request.json()
    update = Update.de_json(payload, bot.bot)
    await bot.update_queue.put(update)

    return {"status": "accepted"}
