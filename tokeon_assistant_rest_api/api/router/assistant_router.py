import logging
import uuid  # Используем для генерации уникальных ID
from fastapi import APIRouter, HTTPException, status, Response

from tokeon_assistant_rest_api.clients.KnowledgeBaseErrors import (
    KnowledgeBaseUpdateInProgressError,
    KnowledgeBaseConnectionError
)
from tokeon_assistant_rest_api.models.models import AskResponse, AskRequest, FeedbackRequest
from tokeon_assistant_rest_api.clients.ya_gpt import answer_from_knowledge_base
assistant_router = APIRouter()
logger = logging.getLogger(__name__)

# --- Endpoints ---
@assistant_router.post(
    "/answers",
    response_model=AskResponse,
    status_code=status.HTTP_201_CREATED, # Используем 201 для создания ресурса "ответ"
    summary="Запросить ответ у ассистента",
    description="Принимает вопрос пользователя, генерирует ответ с помощью RAG и возвращает ответ вместе с уникальным ID."
)
async def ask_assistant(request_data: AskRequest):
    """
    Обрабатывает вопрос пользователя и возвращает ответ.
    Генерирует уникальный `answer_id` для каждого ответа.
    """
    question = request_data.query
    generated_answer_id = uuid.uuid4() # Генерируем ID для этого конкретного ответа

    try:
        logging.info(f"Processing question for answer_id '{generated_answer_id}': '{question}'")
        answer_text = await answer_from_knowledge_base(question)

        if answer_text:
            logging.info(f"Answer found for answer_id '{generated_answer_id}'.")
            logging.debug(f"Answer text for answer_id '{generated_answer_id}': {answer_text}")
        else:
            logging.warning(f"No answer found in knowledge base for answer_id '{generated_answer_id}")
        return AskResponse(answer_id=generated_answer_id, answer=answer_text)
    except KnowledgeBaseUpdateInProgressError as e:
        logging.error(f"Knowledge base is being updated: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="База знаний обновляется, пожалуйста подождите."
        )
    except KnowledgeBaseConnectionError as e:
        logging.error(f"Failed to connect to knowledge base service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось соединиться с сервисом базы знаний."
        )
    except Exception as e:
        logging.error(f"Error processing question for potential answer_id '{generated_answer_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request."
        )


@assistant_router.post(
    "/answers/{answer_id}/feedback",
    status_code=status.HTTP_204_NO_CONTENT, # Устанавливаем статус по умолчанию
    summary="Отправить обратную связь на ответ",
    description="Позволяет пользователю отправить реакцию (positive/negative/neutral) и опциональный комментарий на конкретный ответ, идентифицированный по answer_id."
)
async def submit_feedback(answer_id: uuid.UUID, feedback_data: FeedbackRequest):
    """
    Принимает обратную связь на конкретный ответ.
    Логирует фидбек для дальнейшего анализа.
    """
    try:
        logging.info(
            f"Feedback received for answer_id '{answer_id}': "
            f"Reaction='{feedback_data.feedback_reaction}', "
            f"Comment='{feedback_data.comment if feedback_data.comment else 'N/A'}'. "
        )
        return Response(status_code=status.HTTP_202_ACCEPTED, content="Feedback received successfully.")

    except Exception as e:
        logging.error(f"Error processing feedback for answer_id '{answer_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your feedback."
        )