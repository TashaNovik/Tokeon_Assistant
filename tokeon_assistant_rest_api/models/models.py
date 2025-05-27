import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """
    Request model for submitting a user question.

    Attributes:
        query (str): User's question text. Required, minimum length of 1 character.
    """
    query: str = Field(..., description="Текст вопроса от пользователя", min_length=1)

class AskResponse(BaseModel):
    """
    Response model containing the generated answer and its unique identifier.

    Attributes:
        answer_id (uuid.UUID): Unique identifier for the answer, used for feedback reference.
        answer (Optional[str]): Generated answer text, or None if no answer was found.
    """
    answer_id: uuid.UUID = Field(..., description="Уникальный идентификатор ответа для обратной связи")
    answer: Optional[str] = Field(None, description="Сгенерированный ответ бота или null, если ответ не найден")

class FeedbackRequest(BaseModel):
    """
    Model for submitting user feedback on a bot's answer.

    Attributes:
        feedback_reaction (Literal["positive", "negative", "neutral"]): User's rating of the answer.
        comment (Optional[str]): Optional text comment, max length 1000 characters.
    """
    feedback_reaction: Literal["positive", "negative", "neutral"] = Field(..., description="Оценка ответа")
    comment: Optional[str] = Field(None, description="Опциональный текстовый комментарий", max_length=1000)

