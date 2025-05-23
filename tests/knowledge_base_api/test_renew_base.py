import pytest
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

from knowledge_base_api.clients.renew_base import main, context


@pytest.mark.asyncio
async def test_main(temp_directory, mock_kb_settings, mock_chunks_result):
    with patch('knowledge_base_api.clients.renew_base.knowledge_base_runner') as mock_runner, \
         patch('knowledge_base_api.clients.renew_base.chunking', return_value=mock_chunks_result) as mock_chunking, \
         patch('knowledge_base_api.clients.renew_base.async_send', new_callable=AsyncMock) as mock_async_send, \
         patch('knowledge_base_api.clients.renew_base.context') as mock_context, \
         patch('asyncio.get_event_loop') as mock_get_loop:
        
        mock_runner.return_value = {
            "test_file.txt": temp_directory
        }
        
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock()
        mock_get_loop.return_value = mock_loop
        
        await main(kb_dir=temp_directory)
        
        mock_runner.assert_called_once_with(temp_directory)
        
        mock_chunking.assert_called_once_with(temp_directory, "test_file.txt")
        
        mock_async_send.assert_called_once_with(mock_chunks_result, "test_file.txt", rewrite=True)
        
        mock_loop.run_in_executor.assert_awaited_once()


def test_context(temp_directory, mock_kb_settings):
    with patch('knowledge_base_api.clients.renew_base.knowledge_base_runner') as mock_runner, \
         patch('knowledge_base_api.clients.renew_base.learning_synonims') as mock_learning_synonims, \
         patch('knowledge_base_api.clients.renew_base.os.makedirs') as mock_makedirs, \
         patch('knowledge_base_api.clients.renew_base.open', create=True) as mock_open, \
         patch('knowledge_base_api.clients.renew_base.json.dump') as mock_json_dump:
        
        mock_runner.return_value = {
            "test_file.txt": temp_directory
        }
        
        mock_learning_synonims.return_value = ["token1", "token2", "token3"]
        
        mock_file = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_open.return_value = mock_context_manager
        
        context(kb_dir=temp_directory)
        
        mock_runner.assert_called_once_with(temp_directory)
        
        mock_learning_synonims.assert_called_once_with(temp_directory)
        
        mock_makedirs.assert_called_once()
        
        mock_json_dump.assert_called_once_with(
            ["token1", "token2", "token3"], 
            mock_file, 
            ensure_ascii=False, 
            indent=2
        ) 