from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram_bot.config import settings
import logging
import httpx
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ASKING_QUESTION = 1
AWAITING_FEEDBACK_CHOICE = 2
AWAITING_FEEDBACK_COMMENT = 3


def create_bot() -> Application:
    """
    Create and configure the Telegram Application with handlers and commands.

    Returns:
        Application: Configured Telegram bot application instance.
    """
    bot_token = settings.telegram_token if hasattr(settings, 'telegram_token') else settings.telegram.token

    app = Application.builder() \
        .token(bot_token) \
        .build()

    app.add_handler(CallbackQueryHandler(feedback_button_callback, pattern="^feedback:"))

    conv_handler_ask = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_start)],
        states={
            ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_receive_question)],
            AWAITING_FEEDBACK_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_while_awaiting_feedback_choice)
            ],
            AWAITING_FEEDBACK_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback_comment),
                CommandHandler("skip_comment", skip_feedback_comment)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    app.add_handler(conv_handler_ask)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    bot_commands = [
        BotCommand("start", "Приветственное сообщение"),
        BotCommand("help", "Список доступных команд"),
        BotCommand("ask", "Задать вопрос ассистенту"),
        BotCommand("cancel", "Отменить текущую операцию"),
    ]

    async def post_init(application: Application):
        await application.bot.set_my_commands(bot_commands)

    app.post_init = post_init

    return app


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a greeting message with instructions to start asking questions.

    Args:
        update (Update): Incoming update.
        context (ContextTypes.DEFAULT_TYPE): Context object.
    """
    await update.message.reply_text(
        "👋 Привет!\n"
        "Используй `/ask`, чтобы задать вопрос."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a help message listing available commands.

    Args:
        update (Update): Incoming update.
        context (ContextTypes.DEFAULT_TYPE): Context object.
    """
    await update.message.reply_text(
        "/start — Приветственное сообщение\n"
        "/help  — Список доступных команд\n"
        "/ask   — Задать вопрос ассистенту\n"
        "/cancel— Отменить текущую операцию"
    )


async def ask_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompt user to send their question.

    Args:
        update (Update): Incoming update.
        context (ContextTypes.DEFAULT_TYPE): Context object.

    Returns:
        int: State ASKING_QUESTION to expect user's question.
    """
    await update.message.reply_text("📝 Пожалуйста, отправьте ваш вопрос:")
    return ASKING_QUESTION


async def ask_receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process user's question, query assistant API, and send the answer with feedback buttons.

    Args:
        update (Update): Incoming update.
        context (ContextTypes.DEFAULT_TYPE): Context object.

    Returns:
        int: Next conversation state (AWAITING_FEEDBACK_COMMENT or ConversationHandler.END).
    """
    question = update.message.text
    chat_id = update.message.chat_id

    try:
        assistant_response_data = await ask_assistant_via_api(question)
    except Exception as e:
        logger.error(f"Assistant service failed for question '{question}'", exc_info=e)
        await update.message.reply_text(
            "⚠️ К сожалению, произошла ошибка при получении ответа. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

    if not assistant_response_data or assistant_response_data.get("answer") is None:
        answer_id_for_error = assistant_response_data.get("answer_id") if assistant_response_data else None
        if answer_id_for_error:
            context.user_data['current_answer_id'] = answer_id_for_error
            context.user_data['feedback_message_id_to_edit'] = None
            feedback_prompt_text = "Ассистент не смог дать ответ. Хотите сообщить об ошибке?"
            keyboard = [
                [InlineKeyboardButton("👎 Сообщить об ошибке", callback_data=f"feedback:{answer_id_for_error}:error_report")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            feedback_msg = await update.message.reply_text(feedback_prompt_text, reply_markup=reply_markup)
            context.user_data['feedback_message_id_to_edit'] = feedback_msg.message_id
            return AWAITING_FEEDBACK_COMMENT
        else:
            await update.message.reply_text("⚠️ Ассистент не смог дать ответ, и ID ответа не получен.")
            return ConversationHandler.END

    answer_text = assistant_response_data["answer"]
    answer_id = assistant_response_data["answer_id"]

    context.user_data['current_answer_id'] = answer_id

    await update.message.reply_text(answer_text)

    feedback_prompt_text = "Оцените, пожалуйста, ответ:"
    keyboard = [
        [
            InlineKeyboardButton("👍 Позитивно", callback_data=f"feedback:{answer_id}:positive"),
            InlineKeyboardButton("😐 Нейтрально", callback_data=f"feedback:{answer_id}:neutral"),
            InlineKeyboardButton("👎 Негативно", callback_data=f"feedback:{answer_id}:negative"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    feedback_message = await update.message.reply_text(feedback_prompt_text, reply_markup=reply_markup)
    context.user_data['feedback_message_id_to_edit'] = feedback_message.message_id

    return AWAITING_FEEDBACK_COMMENT


async def ask_assistant_via_api(question: str) -> dict | None:
    """
    Send a question to the assistant API and return the response.

    Args:
        question (str): The question text.

    Returns:
        dict | None: Dictionary containing 'answer' and 'answer_id' or None on failure.
    """
    base_url = os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
    url = f"{base_url}/answers"
    data = {"query": question}
    logger.info(f"Sending question to assistant API: {url} with data: {data}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=httpx.Timeout(60, connect=10))

        response.raise_for_status()
        answer_data = response.json()
        if 'answer' in answer_data and 'answer_id' in answer_data:
            logger.info(f"Received from assistant API: {answer_data}")
            return answer_data
        else:
            logger.error(f"Assistant API response missing 'answer' or 'answer_id'. Received: {answer_data}")
            return {"answer": None, "answer_id": answer_data.get("answer_id")}

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from assistant API: {e.response.status_code} - {e.response.text}")
        try:
            error_data = e.response.json()
            return {"answer": None, "answer_id": error_data.get("answer_id")}
        except:
            pass
        raise
    except Exception as e:
        logger.error(f"Error calling assistant API: {e}")
        raise


async def send_feedback_to_api(answer_id: str, reaction: str, comment: str | None = None) -> bool:
    """
    Send feedback to the backend API.

    Args:
        answer_id (str): The ID of the answer being rated.
        reaction (str): Reaction type (e.g., positive, neutral, negative).
        comment (str | None): Optional textual comment.

    Returns:
        bool: True if feedback was successfully sent, False otherwise.
    """
    base_url = os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
    feedback_url = f"{base_url}/answers/{answer_id}/feedback"
    payload = {"feedback_reaction": reaction, "comment": comment or ""}

    logger.info(f"Sending feedback to {feedback_url} with payload: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(feedback_url, json=payload, timeout=httpx.Timeout(60, connect=10))
            response.raise_for_status()
            logger.info(f"Feedback sent for answer_id {answer_id}. Status: {response.status_code}")
            return True
    except httpx.RequestError as e:
        logger.error(f"Error sending feedback for answer_id {answer_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Feedback API Response status: {e.response.status_code}, body: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending feedback: {e}")
        return False


async def feedback_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """
    Handle feedback button presses and prompt user for optional comment.

    Args:
        update (Update): Incoming update with callback query.
        context (ContextTypes.DEFAULT_TYPE): Context object.

    Returns:
        int | None: Next conversation state or None to end conversation.
    """
    query = update.callback_query
    await query.answer()

    try:
        action_type, answer_id_from_callback, reaction_value = query.data.split(":")
        logger.info(f"Feedback button: {query.data}")
    except ValueError:
        return ConversationHandler.END

    if action_type != "feedback":
        return ConversationHandler.END

    context.user_data['current_answer_id'] = answer_id_from_callback
    context.user_data['current_reaction_for_feedback'] = reaction_value
    feedback_msg_id_to_edit = context.user_data.get('feedback_message_id_to_edit', query.message.message_id if query.message else None)
    chat_id_for_edit = query.message.chat_id if query.message else context.user_data.get('chat_id_for_feedback')

    if not chat_id_for_edit:
        logger.error("Cannot determine chat_id for editing feedback message.")
        return ConversationHandler.END

    new_text_for_feedback_message = ""
    new_reply_markup = None

    if reaction_value == "request_comment":
        new_text_for_feedback_message = "📝 Пожалуйста, напишите ваш комментарий к ответу (или /skip_comment для пропуска):"
    elif reaction_value == "error_report":
        context.user_data['current_reaction_for_feedback'] = "negative" # Пример
        new_text_for_feedback_message = "📝 Пожалуйста, опишите проблему (или /skip_comment для пропуска):"
    else: # positive, neutral, negative
        reaction_display = {
            "positive": "Позитивная оценка 👍",
            "neutral": "Нейтральная оценка 😐",
            "negative": "Негативная оценка 👎"
        }.get(reaction_value, "Оценка")

        new_text_for_feedback_message = (
            f"{reaction_display} принята.\n"
            "📝 Хотите добавить комментарий? Напишите его или используйте /skip_comment, чтобы отправить только оценку."
        )

    if feedback_msg_id_to_edit:
        try:
            await context.bot.edit_message_text(
                text=new_text_for_feedback_message,
                chat_id=chat_id_for_edit,
                message_id=feedback_msg_id_to_edit,
                reply_markup=new_reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to edit feedback message: {e}")

            await context.bot.send_message(chat_id=chat_id_for_edit, text=new_text_for_feedback_message, reply_markup=new_reply_markup)
    elif query.message:
        await query.message.reply_text(new_text_for_feedback_message, reply_markup=new_reply_markup)
    else:
        logger.warning("Could not find message to edit or reply to for feedback prompt.")

        return ConversationHandler.END


    return AWAITING_FEEDBACK_COMMENT


async def receive_feedback_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives a text comment from the user, sends feedback with the comment to the API,
    thanks the user, and ends the conversation.

    If the associated answer ID cannot be determined, prompts the user to start over.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context with user data and bot info.

    Returns:
        int: The next conversation state or ConversationHandler.END to finish.
    """
    comment_text = update.message.text
    answer_id = context.user_data.get('current_answer_id')
    reaction = context.user_data.get('current_reaction_for_feedback', "neutral")

    if not answer_id:
        await update.message.reply_text("Не удалось определить, к какому ответу относится ваш комментарий. Пожалуйста, начните заново с /ask.")
        return ConversationHandler.END

    logger.info(f"Received comment '{comment_text}' for answer_id {answer_id} with reaction {reaction}")
    feedback_sent = await send_feedback_to_api(answer_id, reaction, comment=comment_text)

    if feedback_sent:
        await update.message.reply_text("Спасибо! Ваш комментарий и оценка приняты.")
    else:
        await update.message.reply_text("Не удалось отправить ваш комментарий. Попробуйте позже или используйте /cancel.")

    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END


async def skip_feedback_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Skips the comment input step and sends feedback with only the reaction if it exists.

    If no answer ID or reaction is available, informs the user accordingly.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context with user data and bot info.

    Returns:
        int: The next conversation state or ConversationHandler.END to finish.
    """
    answer_id = context.user_data.get('current_answer_id')
    reaction = context.user_data.get('current_reaction_for_feedback')

    if not answer_id or not reaction or reaction == "request_comment":
        await update.message.reply_text("Нечего пропускать или не выбрана оценка. Используйте /cancel или дайте оценку.")

        return AWAITING_FEEDBACK_COMMENT if reaction == "request_comment" else ConversationHandler.END

    logger.info(f"Skipping comment for answer_id {answer_id}, sending reaction {reaction}")
    feedback_sent = await send_feedback_to_api(answer_id, reaction, comment=None) # comment=None станет ""

    if feedback_sent:
        await update.message.reply_text(f"Спасибо за вашу оценку ({reaction})! Комментарий пропущен.")
    else:
        await update.message.reply_text("Не удалось отправить вашу оценку. Попробуйте позже.")


    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the current conversation, informs the user, and clears the state.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context with user data and bot info.

    Returns:
        int: ConversationHandler.END to end the conversation.
    """
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("❌ Операция отменена.")


    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END

async def handle_text_while_awaiting_feedback_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles text messages received when the bot is expecting the user to press feedback buttons.

    Informs the user to use buttons or commands instead.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context with user data and bot info.

    Returns:
        int: The current state to keep waiting for feedback choice.
    """
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки для оценки ответа или напишите комментарий после нажатия '📝 Оставить комментарий'.\n"
        "Для отмены используйте /cancel."
    )
    return AWAITING_FEEDBACK_CHOICE # Остаемся в этом состоянии

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Я не распознал эту команду или сообщение. "
        "Используйте /help для списка команд или /ask, чтобы задать вопрос."
    )