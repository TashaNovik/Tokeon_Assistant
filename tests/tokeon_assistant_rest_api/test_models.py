import uuid
import pytest
from pydantic import ValidationError
from tokeon_assistant_rest_api.models.models import AskRequest, AskResponse, FeedbackRequest

def test_ask_request_valid():
    req = AskRequest(query="Test question?")
    assert req.query == "Test question?"

def test_ask_request_invalid():
    with pytest.raises(ValidationError):
        AskRequest(query="")

def test_ask_response_valid():
    answer_id = uuid.uuid4()
    resp = AskResponse(answer_id=answer_id, answer="Ответ")
    assert resp.answer_id == answer_id
    assert resp.answer == "Ответ"

def test_feedback_request_valid():
    req = FeedbackRequest(feedback_reaction="positive", comment="Good!")
    assert req.feedback_reaction == "positive"
    assert req.comment == "Good!"

def test_feedback_request_invalid_reaction():
    with pytest.raises(ValidationError):
        FeedbackRequest(feedback_reaction="bad", comment="...")

def test_feedback_request_comment_too_long():
    with pytest.raises(ValidationError):
        FeedbackRequest(feedback_reaction="neutral", comment="a"*1001) 