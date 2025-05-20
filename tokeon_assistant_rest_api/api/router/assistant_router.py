import logging
import uuid  # Используем для генерации уникальных ID
from fastapi import APIRouter, HTTPException, status, Response
from tokeon_assistant_rest_api.models.models import AskResponse, AskRequest, FeedbackRequest
from tokeon_assistant_rest_api      .clients.ya_gpt import answer_from_knowledge_base
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
    """Process a user's question and return a generated answer.

    Generates a unique `answer_id` for each response.

    Args:
        request_data: An AskRequest object containing the user's question.

    Returns:
        AskResponse: The generated answer and its unique identifier.

    Raises:
        HTTPException: If an internal server error occurs during processing.
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
    """Receive user feedback for a specific answer.

    Logs the feedback for further analysis.

    Args:
        answer_id: UUID of the answer being reviewed.
        feedback_data: FeedbackRequest object containing reaction and optional comment.

    Returns:
        Response: HTTP 202 Accepted response indicating successful receipt.

    Raises:
        HTTPException: If an internal server error occurs during feedback processing.
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