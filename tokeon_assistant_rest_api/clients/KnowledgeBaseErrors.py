"""Errors related to the knowledge base operations."""

class KnowledgeBaseError(Exception):
    """Base exception class for all knowledge base related errors."""
    pass

class KnowledgeBaseUpdateInProgressError(KnowledgeBaseError):
    """Raised when the knowledge base is being updated and is temporarily unavailable."""
    def __init__(self, message: str):
        super().__init__(message)


class KnowledgeBaseConnectionError(KnowledgeBaseError):
    """Raised when there's an issue connecting to the knowledge base service."""
    def __init__(self, message: str):
        super().__init__(message)
