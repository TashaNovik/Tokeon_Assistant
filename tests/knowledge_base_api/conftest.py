import pytest
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def mock_kb_settings():
    settings_data = {
        "ya_gpt": {
            "api_key": "test_api_key",
            "folder_id": "test_folder_id",
            "login": "test_login",
            "password": "test_password"
        },
        "qdrant": {
            "host": "test_qdrant_host",
            "port": 6333
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(message)s"
        }
    }
    
    with patch("knowledge_base_api.config.Settings.load") as mock_load:
        from knowledge_base_api.config import Settings, YaGPTConfig, LoggingConfig, QdrantConfig
        
        ya_gpt_config = YaGPTConfig(**settings_data["ya_gpt"])
        qdrant_config = QdrantConfig(**settings_data["qdrant"])
        logging_config = LoggingConfig(**settings_data["logging"])
        settings = Settings(ya_gpt=ya_gpt_config, qdrant=qdrant_config, logging=logging_config)
        
        mock_load.return_value = settings
        yield settings


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as temp:
        temp.write("Тестовый контент для базы знаний.\nЭто тестовый файл.\nТокеон - это компания.")
        temp_path = temp.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("Тестовый контент для базы знаний.\nЭто тестовый файл.\nТокеон - это компания.")
        
        yield temp_dir


@pytest.fixture
def mock_kb_app():
    app = MagicMock(spec=FastAPI)
    app.state = MagicMock()
    return app


@pytest.fixture
def mock_zip_file():
    mock_file = MagicMock()
    mock_file.filename = "test_knowledge_base.zip"
    mock_file.read = AsyncMock(return_value=b"test zip content")
    return mock_file


@pytest.fixture
def mock_qdrant_client():
    mock_client = MagicMock()
    mock_client.create_collection = AsyncMock()
    mock_client.upload_collection = AsyncMock()
    mock_client.get_collection = AsyncMock(return_value={"status": "green"})
    mock_client.search = AsyncMock(return_value=[
        {"id": "1", "score": 0.95, "payload": {"text": "Текст чанка 1", "source": "test_file.txt"}},
        {"id": "2", "score": 0.85, "payload": {"text": "Текст чанка 2", "source": "test_file.txt"}}
    ])
    return mock_client


@pytest.fixture
def mock_chunks_result():
    return {
        "Large": [
            {"id": 1, "vector": [0.1, 0.2, 0.3], "payload": {"text": "Чанк 1"}},
            {"id": 2, "vector": [0.4, 0.5, 0.6], "payload": {"text": "Чанк 2"}}
        ],
        "Small": [
            {"id": 3, "vector": [0.11, 0.21, 0.31], "payload": {"text": "Малый чанк 1"}},
            {"id": 4, "vector": [0.41, 0.51, 0.61], "payload": {"text": "Малый чанк 2"}}
        ]
    } 