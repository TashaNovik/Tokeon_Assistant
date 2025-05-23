from asyncio import to_thread
from tokeon_assistant_rest_api.clients.api import get_token, send_request_to_yagpt
from tokeon_assistant_rest_api.clients.question_synonimizer import result_question, lemmatize_ru
from tokeon_assistant_rest_api.clients.question_processor import question_preparation
import json
from tokeon_assistant_rest_api.config import settings
import logging

logger = logging.getLogger(__name__)

async def answer_from_knowledge_base(raw_question: str) -> str:
    logger.info(f"Question: {raw_question}")
    lemmas = await to_thread(lemmatize_ru, raw_question)
    logger.info(f"Question lemmas: {lemmas}")
    top_question = result_question(" ".join(lemmas))
    logger.info(f"Top question: {top_question}")
    kb_data_for_question = await question_preparation(top_question)  # await
    logger.info(f"KB data for question: {kb_data_for_question}")
    iam = await to_thread(get_token, settings.ya_gpt.api_key)

    answer = await to_thread(
        send_request_to_yagpt,
        iam,
        getUserPrompt(raw_question, kb_data_for_question),
        system_prompt=getSystemPrompt(),
        temperature=0.0,
    )
    logger.info(f"Answer: {answer}")
    return answer

def getSystemPrompt() -> str:
    """
    Generates the system prompt for the Tokeon AI customer support assistant.
    This prompt instructs the LLM on its role, rules, and how to interpret the user prompt (JSON).
    """
    return """Ты — ИИ-ассистент службы поддержки компании "Токеон".
Твоя основная задача — предоставлять точные и полезные ответы на вопросы пользователей, касающиеся продуктов, услуг и процедур компании "Токеон".
Твои ответы должны основываться **ИСКЛЮЧИТЕЛЬНО** на информации, предоставленной в поле "knowledge_base_chunks" JSON-структуры в сообщении пользователя.
Вопрос пользователя находится в поле "user_question" этой же JSON-структуры.

**Строгие правила твоего поведения:**

1.  **Источник информации:** Внимательно изучи содержимое каждого элемента в массиве "knowledge_base_chunks". Каждый элемент представляет собой фрагмент из базы знаний компании "Токеон" и содержит поля "source" (источник фрагмента) и "text_content" (текст фрагмента). Используй **только** "text_content" из этих фрагментов для формирования ответов. Категорически запрещается использовать любые твои общие знания, предположения или информацию из других источников.
2.  **Полнота ответа:** Старайся давать максимально полный и подробный ответ на "user_question" на основе предоставленного "text_content". Если в контексте есть шаги, реквизиты, ссылки или важные детали, обязательно включай их в ответ, как в примере: "Как пополнить счет... 1. Зайдите... 2. Переведите...".
3.  **Если информация отсутствует:** Если в "knowledge_base_chunks" (даже если массив пуст) нет достаточной информации для ответа на "user_question", ты должен четко и вежливо сообщить об этом. Используй одну из следующих фраз:
    *   "К сожалению, я не смог(ла) найти точный ответ на ваш вопрос в базе знаний компании Токеон."
    *   "На данный момент у меня нет информации по вашему запросу в базе знаний. Я передам ваш вопрос специалистам для уточнения."
    *   "Информация по вашему вопросу отсутствует в моей базе знаний. Пожалуйста, попробуйте переформулировать вопрос или обратитесь к другим ресурсам компании."
    Не пытайся угадывать или придумывать ответ.
4.  **Непонятный вопрос:** Если "user_question" неясен, слишком общий или его невозможно соотнести с предоставленным контекстом, вежливо попроси пользователя уточнить свой запрос. Например: "Не могли бы вы, пожалуйста, уточнить ваш вопрос, чтобы я мог(ла) предоставить наиболее релевантную информацию из базы знаний Токеон?"
5.  **Стиль общения:** Будь вежлив, профессионален и дружелюбен. Твоя цель — помочь пользователю.
6.  **Персональные данные:** Не запрашивай и не пытайся собрать никакие персональные данные у пользователя (ФИО, телефон, email, номер договора и т.д.).

Твоя работа очень важна для компании "Токеон" и ее клиентов. Стремись предоставлять качественную поддержку.
"""

def getUserPrompt(raw_question: str, prepared_kb_chunks: list) -> str:
    prompt_data = {
        "user_question": raw_question,
        "knowledge_base_chunks": f"{prepared_kb_chunks}",
    }

    # ensure_ascii=False to correctly handle Cyrillic characters
    # indent=2 for readability during debugging, can be removed for production to save tokens
    user_prompt_json = json.dumps(prompt_data, ensure_ascii=False, indent=2)

    logger.info(f"User prompt JSON: {user_prompt_json}")
    return user_prompt_json