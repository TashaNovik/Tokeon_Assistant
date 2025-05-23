import pytest
import tempfile
import zipfile
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open

import nltk
nltk.download('punkt')

from fastapi import HTTPException
from fastapi.testclient import TestClient

from knowledge_base_api.api.router.knowledge_base_router import knowledge_base_router, update_knowledge_base


@pytest.mark.asyncio
async def test_update_knowledge_base_success(mock_zip_file, mock_kb_settings):
    with patch('knowledge_base_api.api.router.knowledge_base_router.renew_knowledge_base', new_callable=AsyncMock) as mock_renew, \
         patch('knowledge_base_api.api.router.knowledge_base_router.open', create=True) as mock_file_open, \
         patch('knowledge_base_api.api.router.knowledge_base_router.tempfile.mkdtemp', return_value="/tmp/testdir"), \
         patch('knowledge_base_api.api.router.knowledge_base_router.zipfile.ZipFile') as mock_zipfile:
        
        mock_buffer = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_buffer
        mock_file_open.return_value = mock_context
        
        response = await update_knowledge_base(mock_zip_file)
        
        mock_zip_file.read.assert_awaited_once()
        
        mock_zipfile.assert_called_once()
        mock_zipfile.return_value.__enter__.return_value.extractall.assert_called_once_with("/tmp/testdir")
        
        mock_renew.assert_awaited_once_with("/tmp/testdir")
        
        assert response == {"message": "База знаний успешно обновлена."}


@pytest.mark.asyncio
async def test_update_knowledge_base_error(mock_zip_file, mock_kb_settings):
    with patch('knowledge_base_api.api.router.knowledge_base_router.renew_knowledge_base', 
               side_effect=Exception("Test error")) as mock_renew, \
         patch('knowledge_base_api.api.router.knowledge_base_router.open', create=True) as mock_file_open, \
         patch('knowledge_base_api.api.router.knowledge_base_router.tempfile.mkdtemp', return_value="/tmp/testdir"), \
         patch('knowledge_base_api.api.router.knowledge_base_router.zipfile.ZipFile') as mock_zipfile:
        
        mock_buffer = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_buffer
        mock_file_open.return_value = mock_context
        
        with pytest.raises(HTTPException) as exc_info:
            await update_knowledge_base(mock_zip_file)
        
        assert exc_info.value.status_code == 500
        assert str(exc_info.value.detail) == "Test error"


def test_knowledge_base_router_integration(mock_kb_settings):
    from fastapi import FastAPI, status
    
    app = FastAPI()
    app.include_router(knowledge_base_router)
    
    client = TestClient(app)
    
    routes = [route for route in app.routes]
    assert any(route.path == "/knowledge-base/renew" for route in routes)
    
    for route in app.routes:
        if route.path == "/knowledge-base/renew":
            assert route.methods == {"POST"}
            assert route.status_code == status.HTTP_200_OK

def test_upload_file_for_knowledge_base_update(mock_kb_settings):
    from fastapi import FastAPI
    from unittest.mock import MagicMock
    
    with patch('knowledge_base_api.clients.renew_base.main', new_callable=AsyncMock) as mock_renew, \
         patch('nltk.download') as mock_nltk_download, \
         patch('nltk.data.find') as mock_nltk_find, \
         patch('knowledge_base_api.api.router.knowledge_base_router.open', create=True) as mock_file_open, \
         patch('knowledge_base_api.api.router.knowledge_base_router.tempfile.mkdtemp', return_value="/tmp/testdir"), \
         patch('knowledge_base_api.api.router.knowledge_base_router.zipfile.ZipFile') as mock_zipfile:
        mock_renew.return_value = None
        mock_nltk_download.return_value = None
        mock_nltk_find.return_value = "/tmp/nltk"
        mock_buffer = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_buffer
        mock_file_open.return_value = mock_context
        
        app = FastAPI()
        app.include_router(knowledge_base_router)
        client = TestClient(app)
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            temp_zip_path = temp_zip.name
            with zipfile.ZipFile(temp_zip_path, 'w') as zip_ref:
                zip_ref.writestr("test.txt", "This is a test file content")
                zip_ref.writestr("ortho_context.tab", "")
                zip_ref.writestr("collocations.tab", "")
                zip_ref.writestr("sent_starters.txt", "")
                zip_ref.writestr("abbrev_types.txt", "")
            with open(temp_zip_path, 'rb') as f:
                files = {"zip_file": ("test.zip", f, "application/zip")}
                response = client.post("/knowledge-base/renew", files=files)
            os.unlink(temp_zip_path)
        if response.status_code != 200:
            print("Response status:", response.status_code)
            print("Response body:", response.text)
        assert response.status_code == 200
        assert response.json() == {"message": "База знаний успешно обновлена."} 