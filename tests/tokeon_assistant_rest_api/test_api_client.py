import pytest
from unittest.mock import patch, MagicMock
from tokeon_assistant_rest_api.clients import api

def test_get_token_success():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"iamToken": "test_token"}
        mock_post.return_value = mock_response
        token = api.get_token("oauth")
        assert token == "test_token"

def test_get_token_fail():
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("fail")
        with pytest.raises(Exception):
            api.get_token("oauth")

def test_send_request_to_yagpt_success():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Ответ"}}
                ]
            }
        }
        mock_post.return_value = mock_response
        result = api.send_request_to_yagpt("iam", "prompt", folder_id="folder")
        assert result == "Ответ"

def test_send_request_to_yagpt_fail():
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("fail")
        with pytest.raises(Exception):
            api.send_request_to_yagpt("iam", "prompt", folder_id="folder") 