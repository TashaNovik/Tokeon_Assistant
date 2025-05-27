"""Client for the Tokeon Assistant REST API."""

import logging
import os
from typing import Dict, Optional, Any, Union

import httpx

logger = logging.getLogger(__name__)


class TokeonAssistantClient:
    """Client for interacting with the Tokeon Assistant REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 60):
        """
        Initialize the Tokeon Assistant API client.
        
        Args:
            base_url: Base URL for the Tokeon Assistant API. If not provided, uses environment variables.
            timeout: Timeout for API requests in seconds.
        """
        self.base_url = base_url or os.getenv("TOKEON_ASSISTANT_REST_API_URL", "http://tokeon_assistant_rest_api:8001")
        self.timeout = timeout
        logger.info(f"Initialized Tokeon Assistant client with base URL: {self.base_url}")
        
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Send a question to the assistant API and get the answer.
        
        Args:
            question: The question to ask
            
        Returns:
            Dict containing 'answer' and 'answer_id'
            
        Raises:
            httpx.HTTPStatusError: If the API returns a 4xx/5xx status code
            Exception: For other errors
        """
        url = f"{self.base_url}/answers"
        data = {"query": question}
        logger.info(f"Sending question to assistant API: {url} with data: {data}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    json=data, 
                    timeout=httpx.Timeout(self.timeout, connect=10)
                )

            response.raise_for_status()  # Raises exception for 4xx/5xx codes
            answer_data = response.json()
            
            # Validate response structure
            if 'answer' in answer_data and 'answer_id' in answer_data:
                logger.info(f"Received from assistant API: {answer_data}")
                return answer_data
            else:
                logger.error(f"Assistant API response missing 'answer' or 'answer_id'. Received: {answer_data}")
                # Return a structure with None to handle at the caller level
                return {"answer": None, "answer_id": answer_data.get("answer_id")}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from assistant API: {e.response.status_code} - {e.response.text}")
            # Try to extract answer_id from error body if present
            try:
                error_data = e.response.json()
                return {"answer": None, "answer_id": error_data.get("answer_id")}
            except:  # noqa E722
                pass
            raise  # Re-raise the exception if we couldn't extract ID
        except Exception as e:
            logger.error(f"Error calling assistant API: {e}")
            raise
            
    async def send_feedback(self, answer_id: str, reaction: str, comment: Optional[str] = None) -> bool:
        """
        Send feedback about an answer to the assistant API.
        
        Args:
            answer_id: ID of the answer to provide feedback for
            reaction: The reaction (positive or negative)
            comment: Optional comment with additional feedback
            
        Returns:
            bool: True if feedback was successfully sent
            
        Raises:
            httpx.HTTPStatusError: If the API returns a 4xx/5xx status code
            Exception: For other errors
        """
        url = f"{self.base_url}/answers/{answer_id}/feedback"
        
        # Подготавливаем данные для отправки согласно формату FeedbackRequest
        data = {
            "feedback_reaction": reaction
        }
        
        if comment is not None:
            data["comment"] = comment
            
        logger.info(f"Sending feedback to assistant API: {url} with data: {data}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    json=data, 
                    timeout=httpx.Timeout(self.timeout, connect=10)
                )
                
            response.raise_for_status()
            logger.info(f"Feedback successfully sent for answer_id: {answer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending feedback for answer_id {answer_id}: {e}")
            return False
