import pytest
import os
import tempfile
import zipfile
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from knowledge_base_api.main import create_app
from knowledge_base_api.api.router.knowledge_base_router import knowledge_base_router

@pytest.fixture
def test_app(mock_kb_settings):
    with patch('knowledge_base_api.api.router.knowledge_base_router.renew_knowledge_base', 
               new_callable=AsyncMock) as mock_renew:
        mock_renew.return_value = None
        
        app = create_app()
        yield app, mock_renew


@pytest.mark.asyncio
@pytest.mark.integration
async def test_knowledge_base_update_flow(mock_kb_settings):
    with patch('knowledge_base_api.api.router.knowledge_base_router.renew_knowledge_base', new_callable=AsyncMock) as mock_renew:
        mock_renew.return_value = {"message": "База знаний успешно обновлена"}
        
        app = create_app()
        
        client = TestClient(app)
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'w') as zip_ref:
                zip_ref.writestr("test.txt", "This is a test file content")
            
            with open(temp_zip_path, 'rb') as f:
                files = {"zip_file": ("test.zip", f, "application/zip")}
                response = client.post("/knowledge-base/renew", files=files)
            
            os.unlink(temp_zip_path)
        
        if response.status_code != 200:
            print("Response status:", response.status_code)
            print("Response body:", response.text)
        assert response.status_code == 200
        assert "message" in response.json()
        
        mock_renew.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_knowledge_base_update_error_handling(mock_kb_settings):
    with patch('knowledge_base_api.api.router.knowledge_base_router.renew_knowledge_base', 
               side_effect=Exception("Test error")) as mock_renew:
        
        app = create_app()
        
        client = TestClient(app)
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'w') as zip_ref:
                zip_ref.writestr("test.txt", "This is a test file content")
            
            with open(temp_zip_path, 'rb') as f:
                files = {"zip_file": ("test.zip", f, "application/zip")}
                response = client.post("/knowledge-base/renew", files=files)
            
            os.unlink(temp_zip_path)
        
        if response.status_code != 500:
            print("Response status:", response.status_code)
            print("Response body:", response.text)
        assert response.status_code == 500
        assert "detail" in response.json()
        
        mock_renew.assert_awaited_once()


@pytest.mark.integration
def test_health_endpoint_integration(mock_kb_settings):
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 