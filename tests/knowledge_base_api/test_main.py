import pytest
import logging
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from knowledge_base_api.main import create_app, configure_logging

def test_configure_logging():
    with patch('logging.basicConfig') as mock_basic_config:
        configure_logging()
        
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO
        assert kwargs["format"] == "%(asctime)s %(levelname)s %(name)s: %(message)s"


def test_create_app(mock_kb_settings):
    with patch('knowledge_base_api.main.configure_logging') as mock_configure_logging:
        with patch('knowledge_base_api.main.knowledge_base_router') as mock_router:
            app = create_app()
            
            mock_configure_logging.assert_called_once()
            
            assert isinstance(app, FastAPI)
            assert app.title == "Knowledge Base API"
            assert app.description == "API for managing knowledge bases"
            assert app.version == "1.0.0"
            
            assert any(route.path == "/health" for route in app.routes)


def test_health_endpoint(mock_kb_settings):
    with patch('knowledge_base_api.main.knowledge_base_router'):
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_include_router(mock_kb_settings):
    with patch('knowledge_base_api.main.knowledge_base_router') as mock_router:
        app = create_app()
        client = TestClient(app)
        
        assert any(route for route in app.routes if getattr(route, "path", None) == "/health")
        
        response = client.get("/health")
        assert response.status_code == 200 