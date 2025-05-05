from asyncio import to_thread
from app.clients.api import get_token, send_request_to_yagpt
from app.clients.question_synonimizer import result_question, lemmatize_ru
from app.clients.question_processor import question_preparation

from app.config import settings


async def answer_from_knowledge_base(raw_q: str) -> str:
    lemmas = await to_thread(lemmatize_ru, raw_q)
    top_q = result_question(" ".join(lemmas))
    prepared = await question_preparation(top_q)  # await
    iam = await to_thread(get_token, settings.ya_gpt.api_key)
    answer = await to_thread(
        send_request_to_yagpt,
        iam,
        prepared,
        system_prompt=f"Answer precisely: {raw_q}",
        temperature=0.0,
    )
    return answer
