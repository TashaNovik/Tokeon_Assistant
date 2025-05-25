"""
telegram_bot/api/handlers/rating.py
-----------------------------------
Handles user feedback interactions:
- handle_rating   — triggered when user presses 👍😐👎
- handle_comment  — triggered when user writes a comment after rating
- skip_comment    — triggered when user sends /skip to skip commenting
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.getcwd()))

from telegram import Update
from telegram.ext import ContextTypes

from db.db import AsyncSessionLocal
from db.repository.rating_repository import RatingRepository
from db.repository.comment_repository import CommentRepository


async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes rating button callback with format `rate:<message_id>:<type>`.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context object with user_data.

    Side Effects:
        - Stores the rating in the database.
        - Sets `awaiting_comment_for_id` in user_data.
        - Sends a follow-up prompt in Russian.
    """
    q = update.callback_query
    await q.answer()

    parts = q.data.split(":", 2)
    if len(parts) != 3 or parts[0] != "rate":
        return

    _, msg_id_str, rating_type = parts
    try:
        message_id = int(msg_id_str)
    except ValueError:
        return

    user_id = update.effective_user.id

    async with AsyncSessionLocal() as session:
        rating = await RatingRepository.add_rating_async(
            session=session,
            user_id=user_id,
            message_id=message_id,
            rating_type=rating_type,
        )
        context.user_data["awaiting_comment_for_id"] = rating.id

    await q.edit_message_reply_markup(reply_markup=None)

    if rating_type == "positive":
        txt = (
            "👍 Спасибо за положительную оценку!\n"
            "Расскажите, пожалуйста, что именно понравилось (или отправьте /skip)."
        )
    elif rating_type == "neutral":
        txt = (
            "😐 Спасибо, мы ценим ваш отзыв.\n"
            "Напишите, как улучшить ответ (или /skip)."
        )
    else:
        txt = (
            "👎 Жаль, что ответ не устроил.\n"
            "Опишите проблему, пожалуйста (или /skip)."
        )
    await q.message.reply_text(txt)


async def handle_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles comment text sent by user after a rating.

    Args:
        update (Update): Incoming Telegram message with comment.
        context (ContextTypes.DEFAULT_TYPE): Context containing user_data.

    Side Effects:
        - Saves the comment in the database.
        - Clears `awaiting_comment_for_id` from user_data.
        - Sends a confirmation message in Russian.
    """
    rating_id = context.user_data.get("awaiting_comment_for_id")
    if not rating_id:
        return

    comment_text = update.message.text

    async with AsyncSessionLocal() as session:
        await CommentRepository.add_comment_async(session, rating_id, comment_text)

    context.user_data.pop("awaiting_comment_for_id", None)
    await update.message.reply_text("Спасибо, ваш комментарий сохранён.")


async def skip_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /skip command to cancel pending comment.

    Args:
        update (Update): Telegram update containing /skip.
        context (ContextTypes.DEFAULT_TYPE): Context with user_data.

    Side Effects:
        - Removes `awaiting_comment_for_id` if present.
        - Responds in Russian with appropriate message.
    """
    if context.user_data.pop("awaiting_comment_for_id", None):
        await update.message.reply_text("Хорошо, пропускаем комментарий.")
    else:
        await update.message.reply_text(
            "Сейчас нет запроса на комментарий, который можно пропустить."
        )
