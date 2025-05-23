from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler, # Добавлено
    filters
)
from telegram_bot.config import settings # Предполагается, что settings.telegram.token существует
import logging
import httpx
import os

# Настройка логирования, если еще не настроено глобально
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Состояния для ConversationHandler
ASKING_QUESTION = 1 # Было ASKING
AWAITING_FEEDBACK_CHOICE = 2 # Новое состояние для ожидания нажатия кнопки фидбека
AWAITING_FEEDBACK_COMMENT = 3 # Новое состояние для ожидания текстового комментария

# URL вашего API для фидбека (используется в send_feedback_to_api)
# ASSISTANT_API_BASE_URL = os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
# Перенесем получение base_url в сами функции, чтобы избежать глобальных переменных здесь, если не нужны


def create_bot() -> Application:
    """
    Create and configure the Telegram Application with command handlers.
    """
    # Используем ваш settings.telegram.token
    # Если settings - это объект, а не модуль, то settings.telegram_token
    # или как у вас там настроено. Для примера буду считать, что это работает.
    bot_token = settings.telegram_token if hasattr(settings, 'telegram_token') else settings.telegram.token

    app = Application.builder() \
        .token(bot_token) \
        .build()

    # Обработчик для кнопок фидбека (должен быть добавлен до ConversationHandler, если он его перехватывает)
    # Лучше сделать его частью ConversationHandler или отдельным, если ConversationHandler не мешает
    app.add_handler(CallbackQueryHandler(feedback_button_callback, pattern="^feedback:"))


    conv_handler_ask = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_start)],
        states={
            ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_receive_question)],
            AWAITING_FEEDBACK_CHOICE: [ # Это состояние может быть не нужно, если кнопки обрабатываются вне ConvHandler
                # CallbackQueryHandler(feedback_button_callback, pattern="^feedback:"), # Уже добавлен глобально
                # Можно добавить MessageHandler, если пользователь напишет что-то вместо нажатия кнопки
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_while_awaiting_feedback_choice)
            ],
            AWAITING_FEEDBACK_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback_comment),
                CommandHandler("skip_comment", skip_feedback_comment) # Команда для пропуска комментария
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        # allow_reentry=True # Раскомментируйте, если нужно
        # per_message=False # Важно для CallbackQueryHandler внутри ConversationHandler
    )
    app.add_handler(conv_handler_ask)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    # app.add_handler(CommandHandler("cancel", cancel_conversation)) # Уже в fallbacks

    # Обработчик для неизвестных команд или текста вне диалогов
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Устанавливаем команды бота
    bot_commands = [
        BotCommand("start", "Приветственное сообщение"),
        BotCommand("help", "Список доступных команд"),
        BotCommand("ask", "Задать вопрос ассистенту"),
        BotCommand("cancel", "Отменить текущую операцию"),
    ]
    # Используем context.bot.set_my_commands в post_init, если нужно, или так, если версия позволяет
    # await app.bot.set_my_commands(bot_commands) # Это нужно делать в async функции или post_init

    async def post_init(application: Application):
        await application.bot.set_my_commands(bot_commands)

    app.post_init = post_init


    return app


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет!\n"
        "Используй `/ask`, чтобы задать вопрос."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — Приветственное сообщение\n"
        "/help  — Список доступных команд\n"
        "/ask   — Задать вопрос ассистенту\n"
        "/cancel— Отменить текущую операцию"
    )

async def ask_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📝 Пожалуйста, отправьте ваш вопрос:")
    return ASKING_QUESTION


async def ask_receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает вопрос, запрашивает ответ у API и отправляет его с кнопками фидбека.
    """
    question = update.message.text
    chat_id = update.message.chat_id # Для возможной отправки ошибок или доп. сообщений

    try:
        # ask_assistant_via_api теперь должен возвращать словарь с 'answer' и 'answer_id'
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
            context.user_data['feedback_message_id_to_edit'] = None # Нечего редактировать для ответа
            feedback_prompt_text = "Ассистент не смог дать ответ. Хотите сообщить об ошибке?"
            keyboard = [
                [InlineKeyboardButton("👎 Сообщить об ошибке", callback_data=f"feedback:{answer_id_for_error}:error_report")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            feedback_msg = await update.message.reply_text(feedback_prompt_text, reply_markup=reply_markup)
            context.user_data['feedback_message_id_to_edit'] = feedback_msg.message_id
            return AWAITING_FEEDBACK_COMMENT # Ожидаем комментарий к ошибке
        else:
            await update.message.reply_text("⚠️ Ассистент не смог дать ответ, и ID ответа не получен.")
            return ConversationHandler.END


    answer_text = assistant_response_data["answer"]
    answer_id = assistant_response_data["answer_id"]

    # Сохраняем answer_id для использования в других состояниях (например, при получении комментария)
    context.user_data['current_answer_id'] = answer_id

    # Отправляем ответ ассистента
    await update.message.reply_text(answer_text)

    # Отправляем сообщение с кнопками фидбека
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
    # Сохраняем ID сообщения с кнопками, чтобы его можно было отредактировать
    context.user_data['feedback_message_id_to_edit'] = feedback_message.message_id

    return AWAITING_FEEDBACK_COMMENT # Переходим в состояние ожидания фидбека (комментария или выбора кнопки)

async def ask_assistant_via_api(question: str) -> dict | None:
    """
    Отправляет вопрос на API ассистента и возвращает словарь с 'answer' и 'answer_id'.
    """
    base_url = os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
    url = f"{base_url}/answers" # Убедитесь, что это правильный эндпоинт для ЗАПРОСА ответа
    data = {"query": question}
    logger.info(f"Sending question to assistant API: {url} with data: {data}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=httpx.Timeout(60, connect=10))

        response.raise_for_status() # Вызовет исключение для 4xx/5xx кодов
        answer_data = response.json()
        # Убедитесь, что ваше API возвращает 'answer' и 'answer_id'
        if 'answer' in answer_data and 'answer_id' in answer_data:
            logger.info(f"Received from assistant API: {answer_data}")
            return answer_data
        else:
            logger.error(f"Assistant API response missing 'answer' or 'answer_id'. Received: {answer_data}")
            # Можно вернуть структуру с None, чтобы обработать выше
            return {"answer": None, "answer_id": answer_data.get("answer_id")}

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from assistant API: {e.response.status_code} - {e.response.text}")
        # Попытка извлечь answer_id из тела ошибки, если он там есть
        try:
            error_data = e.response.json()
            return {"answer": None, "answer_id": error_data.get("answer_id")}
        except: # noqa E722
            pass
        raise # Перевыбрасываем исключение, если не смогли извлечь ID
    except Exception as e:
        logger.error(f"Error calling assistant API: {e}")
        raise


async def send_feedback_to_api(answer_id: str, reaction: str, comment: str | None = None) -> bool:
    """Отправляет фидбек на ваш бэкенд."""
    base_url = os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
    feedback_url = f"{base_url}/answers/{answer_id}/feedback"
    payload = {"feedback_reaction": reaction}
    # Ваш API ожидает "comment": "string1", даже если он пустой, может быть "comment": ""
    payload["comment"] = comment if comment is not None else ""

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
    query = update.callback_query
    await query.answer()

    try:
        action_type, answer_id_from_callback, reaction_value = query.data.split(":")
        logger.info(f"Feedback button: {query.data}")
    except ValueError:
        # ... (обработка ошибки как раньше) ...
        return ConversationHandler.END # или None, если не в диалоге

    if action_type != "feedback":
        # ... (обработка ошибки как раньше) ...
        return ConversationHandler.END # или None

    context.user_data['current_answer_id'] = answer_id_from_callback
    context.user_data['current_reaction_for_feedback'] = reaction_value
    feedback_msg_id_to_edit = context.user_data.get('feedback_message_id_to_edit', query.message.message_id if query.message else None)

    chat_id_for_edit = query.message.chat_id if query.message else context.user_data.get('chat_id_for_feedback') # Сохраняйте chat_id в user_data если нужно

    if not chat_id_for_edit: # Если не можем определить chat_id, это проблема
        logger.error("Cannot determine chat_id for editing feedback message.")
        return ConversationHandler.END # Завершаем, так как не можем продолжить осмысленно

    new_text_for_feedback_message = ""
    new_reply_markup = None

    if reaction_value == "request_comment":
        new_text_for_feedback_message = "📝 Пожалуйста, напишите ваш комментарий к ответу (или /skip_comment для пропуска):"
        # Кнопки уже убраны или будут убраны, так как мы ждем текст
    elif reaction_value == "error_report":
        # Пользователь нажал "Сообщить об ошибке"
        # current_reaction_for_feedback уже установлен как "error_report"
        # Можно переопределить на "negative" для API, если API не знает "error_report"
        context.user_data['current_reaction_for_feedback'] = "negative" # Пример
        new_text_for_feedback_message = "📝 Пожалуйста, опишите проблему (или /skip_comment для пропуска):"
    else: # positive, neutral, negative
        # Оценка выбрана, теперь предлагаем оставить комментарий или пропустить
        reaction_display = {
            "positive": "Позитивная оценка 👍",
            "neutral": "Нейтральная оценка 😐",
            "negative": "Негативная оценка 👎"
        }.get(reaction_value, "Оценка")

        new_text_for_feedback_message = (
            f"{reaction_display} принята.\n"
            "📝 Хотите добавить комментарий? Напишите его или используйте /skip_comment, чтобы отправить только оценку."
        )
        # Можно оставить кнопки "Пропустить комментарий" и "Отмена", если нужно
        # keyboard_skip = [[InlineKeyboardButton("⏩ Пропустить комментарий", callback_data=f"feedback:{answer_id_from_callback}:skip_direct")]]
        # new_reply_markup = InlineKeyboardMarkup(keyboard_skip) # Если хотим кнопку пропуска

    # Редактируем сообщение с кнопками
    if feedback_msg_id_to_edit:
        try:
            await context.bot.edit_message_text(
                text=new_text_for_feedback_message,
                chat_id=chat_id_for_edit,
                message_id=feedback_msg_id_to_edit,
                reply_markup=new_reply_markup # Убираем старые кнопки или ставим новые (например, "Пропустить")
            )
        except Exception as e:
            logger.error(f"Failed to edit feedback message: {e}")
            # Если не удалось отредактировать, можем отправить новое сообщение
            await context.bot.send_message(chat_id=chat_id_for_edit, text=new_text_for_feedback_message, reply_markup=new_reply_markup)
    elif query.message: # Если ID не был сохранен, но есть текущее сообщение
        await query.message.reply_text(new_text_for_feedback_message, reply_markup=new_reply_markup)
    else: # Крайний случай, если вообще нет информации о сообщении
        logger.warning("Could not find message to edit or reply to for feedback prompt.")
        # Не можем продолжить осмысленно без сообщения пользователю
        return ConversationHandler.END


    return AWAITING_FEEDBACK_COMMENT # Всегда переходим в ожидание комментария (или /skip_comment)


async def receive_feedback_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает текстовый комментарий, отправляет фидбек с комментарием."""
    comment_text = update.message.text
    answer_id = context.user_data.get('current_answer_id')
    reaction = context.user_data.get('current_reaction_for_feedback', "neutral") # По умолчанию, если не было кнопки

    if not answer_id:
        await update.message.reply_text("Не удалось определить, к какому ответу относится ваш комментарий. Пожалуйста, начните заново с /ask.")
        return ConversationHandler.END

    logger.info(f"Received comment '{comment_text}' for answer_id {answer_id} with reaction {reaction}")
    feedback_sent = await send_feedback_to_api(answer_id, reaction, comment=comment_text)

    if feedback_sent:
        await update.message.reply_text("Спасибо! Ваш комментарий и оценка приняты.")
    else:
        await update.message.reply_text("Не удалось отправить ваш комментарий. Попробуйте позже или используйте /cancel.")

    # Очистка user_data
    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END


async def skip_feedback_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропускает шаг ввода комментария и отправляет фидбек только с реакцией (если была)."""
    answer_id = context.user_data.get('current_answer_id')
    reaction = context.user_data.get('current_reaction_for_feedback') # Должна быть установлена кнопкой

    if not answer_id or not reaction or reaction == "request_comment":
        await update.message.reply_text("Нечего пропускать или не выбрана оценка. Используйте /cancel или дайте оценку.")
        # Остаемся в том же состоянии, если реакция была request_comment,
        # иначе можно завершить диалог, если просто нет ID
        return AWAITING_FEEDBACK_COMMENT if reaction == "request_comment" else ConversationHandler.END

    logger.info(f"Skipping comment for answer_id {answer_id}, sending reaction {reaction}")
    feedback_sent = await send_feedback_to_api(answer_id, reaction, comment=None) # comment=None станет ""

    if feedback_sent:
        await update.message.reply_text(f"Спасибо за вашу оценку ({reaction})! Комментарий пропущен.")
    else:
        await update.message.reply_text("Не удалось отправить вашу оценку. Попробуйте позже.")

    # Очистка user_data
    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущую операцию в ConversationHandler."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("❌ Операция отменена.")

    # Очистка user_data при отмене
    if 'current_answer_id' in context.user_data: del context.user_data['current_answer_id']
    if 'current_reaction_for_feedback' in context.user_data: del context.user_data['current_reaction_for_feedback']
    if 'feedback_message_id_to_edit' in context.user_data: del context.user_data['feedback_message_id_to_edit']

    return ConversationHandler.END

async def handle_text_while_awaiting_feedback_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает текст, когда ожидается нажатие кнопки фидбека."""
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