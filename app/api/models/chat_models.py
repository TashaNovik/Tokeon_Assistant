import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field

# --- Pydantic Модели ---

class AskRequest(BaseModel):
    """Модель запроса для получения ответа."""
    query: str = Field(..., description="Текст вопроса от пользователя", min_length=1)

class AskResponse(BaseModel):
    """Модель ответа со сгенерированным текстом и ID ответа."""
    answer_id: uuid.UUID = Field(..., description="Уникальный идентификатор ответа для обратной связи")
    answer: Optional[str] = Field(None, description="Сгенерированный ответ бота или null, если ответ не найден")

class FeedbackRequest(BaseModel):
    """Модель для отправки обратной связи на ответ бота."""
    feedback_reaction: Literal["positive", "negative", "neutral"] = Field(..., description="Оценка ответа")
    comment: Optional[str] = Field(None, description="Опциональный текстовый комментарий", max_length=1000)

