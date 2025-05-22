import logging
import os
import httpx
from typing import Optional
from tokeon_assistant_rest_api.clients.KnowledgeBaseErrors import (
    KnowledgeBaseUpdateInProgressError,
    KnowledgeBaseConnectionError
)

logger = logging.getLogger(__name__)

class KnowledgeBaseClient:
    """Client for interacting with the Knowledge Base API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Knowledge Base API client.
        
        Args:
            base_url: Base URL for the Knowledge Base API. If not provided, uses environment variables.
        """
        self.base_url = os.getenv("KNOWLEDGE_BASE_API_URL", "http://knowledge_base_api:8002")
        logger.info(f"Initialized Knowledge Base client with base URL: {self.base_url}")
    
    async def prepare_question(self, question: str) -> str:
        """
        Get knowledge base data prepared for a specific question.
        
        Args:
            question: The question to prepare knowledge base data for
            
        Returns:
            str: Relevant knowledge base data for the question
            
        Raises:
            KnowledgeBaseUpdateInProgressError: If the knowledge base is being updated (model not found)
            KnowledgeBaseConnectionError: If there is a problem connecting to the knowledge base API
            Exception: For other errors
        """
        url = f"{self.base_url}/knowledge-base/prepare-question"
        
        try:
            logger.info(f"Sending question to knowledge base API: {question}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"question": question})
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Error from knowledge base API: {error_text}")
                    
                    # Specific handling for service unavailable (knowledge base updating)
                    if response.status_code == 503:
                        raise KnowledgeBaseUpdateInProgressError(response.json().get("detail", "База знаний обновляется, пожалуйста подождите."))
                    
                    # Generic error handling
                    raise Exception(f"Failed to get knowledge base data: {error_text}")
                
                result = response.json()
                logger.info(f"Received knowledge base data: {result['data'][:100]}...")
                return result['data']
        except httpx.RequestError as e:
            logger.error(f"Error connecting to knowledge base API: {e}")
            raise KnowledgeBaseConnectionError(f"Не удалось соединиться с сервисом базы знаний: {e}")
        except Exception as e:
            # Re-raise domain-specific errors
            if isinstance(e, (KnowledgeBaseUpdateInProgressError, KnowledgeBaseConnectionError)):
                raise
            
            logger.error(f"Error getting knowledge base data: {e}")
            raise
