import uuid
import pytest
from fastapi.testclient import TestClient
from tokeon_assistant_rest_api.main import create_app
from unittest.mock import patch, AsyncMock

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_ask_assistant_success(client):
    with patch("tokeon_assistant_rest_api.api.router.assistant_router.answer_from_knowledge_base", new_callable=AsyncMock) as mock_answer:
        mock_answer.return_value = "Ответ ассистента"
        response = client.post("/answers", json={"query": "Что такое Python?"})
        assert response.status_code == 201
        data = response.json()
        assert "answer_id" in data
        assert data["answer"] == "Ответ ассистента"

def test_ask_assistant_internal_error(client):
    with patch("tokeon_assistant_rest_api.clients.ya_gpt.answer_from_knowledge_base", new_callable=AsyncMock) as mock_answer:
        mock_answer.side_effect = Exception("fail")
        response = client.post("/answers", json={"query": "Что такое Python?"})
        assert response.status_code == 500
        assert response.json()["detail"]

def test_submit_feedback_success(client):
    answer_id = str(uuid.uuid4())
    payload = {"feedback_reaction": "positive", "comment": "Отлично!"}
    response = client.post(f"/answers/{answer_id}/feedback", json=payload)
    assert response.status_code == 202
    assert response.text == "Feedback received successfully." 