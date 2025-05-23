import pytest
import logging
from unittest.mock import patch, AsyncMock, MagicMock

from knowledge_base_api.clients.qdrant_sender import async_send

logger = logging.getLogger("knowledge_base_api.clients.qdrant_sender")


@pytest.mark.asyncio
async def test_async_send_new_collection(mock_chunks_result, mock_kb_settings):
    with patch('knowledge_base_api.clients.qdrant_sender.AsyncQdrantClient') as mock_qdrant_client_class:
        mock_client = AsyncMock()
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections = AsyncMock(return_value=mock_collections)
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock()
        mock_client.close = AsyncMock()
        mock_qdrant_client_class.return_value = mock_client
        
        await async_send(mock_chunks_result, "test_file.txt", rewrite=True)
        
        mock_qdrant_client_class.assert_called_once()
        
        mock_client.create_collection.assert_called_once()
        
        assert mock_client.upsert.await_count == 2
        
        mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_send_rewrite_collection(mock_chunks_result, mock_kb_settings):
    with patch('knowledge_base_api.clients.qdrant_sender.AsyncQdrantClient') as mock_qdrant_client_class:
        mock_client = AsyncMock()
        mock_collection = MagicMock()
        mock_collection.name = "test_file.txt"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_client.get_collections = AsyncMock(return_value=mock_collections)
        mock_client.delete_collection = AsyncMock()
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock()
        mock_client.close = AsyncMock()
        mock_qdrant_client_class.return_value = mock_client
        
        await async_send(mock_chunks_result, "test_file.txt", rewrite=True)
        
        mock_client.delete_collection.assert_called_once_with("test_file.txt")
        mock_client.create_collection.assert_called_once()
        
        assert mock_client.upsert.await_count == 2
        
        mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_send_no_rewrite(mock_chunks_result, mock_kb_settings):
    with patch('knowledge_base_api.clients.qdrant_sender.AsyncQdrantClient') as mock_qdrant_client_class, \
         patch('builtins.print') as mock_print:
        mock_client = AsyncMock()
        mock_collection = MagicMock()
        mock_collection.name = "test_file.txt"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_client.get_collections = AsyncMock(return_value=mock_collections)
        mock_client.delete_collection = AsyncMock()
        mock_client.create_collection = AsyncMock()
        mock_client.upsert = AsyncMock()
        mock_client.close = AsyncMock()
        mock_qdrant_client_class.return_value = mock_client
        
        await async_send(mock_chunks_result, "test_file.txt", rewrite=False)
        
        mock_client.delete_collection.assert_not_called()
        
        mock_client.create_collection.assert_not_called()
        
        mock_print.assert_called_with("Collection test_file.txt exists. passing")
        
        mock_client.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_async_send_create_collection_error(mock_chunks_result, mock_kb_settings):
    with patch('knowledge_base_api.clients.qdrant_sender.AsyncQdrantClient') as mock_qdrant_client_class, \
         patch('builtins.print') as mock_print:
        mock_client = AsyncMock()
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections = AsyncMock(return_value=mock_collections)
        mock_client.create_collection = AsyncMock(side_effect=Exception("Failed to create collection"))
        mock_client.close = AsyncMock()
        mock_qdrant_client_class.return_value = mock_client
        
        await async_send(mock_chunks_result, "test_file.txt", rewrite=True)
        
        mock_print.assert_called_with("Error processing test_file.txt: Failed to create collection")
        
        mock_client.close.assert_awaited_once() 