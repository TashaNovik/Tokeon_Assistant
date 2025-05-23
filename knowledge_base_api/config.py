import yaml
import os
from pydantic import BaseModel

class YaGPTConfig(BaseModel):
    api_key: str
    folder_id: str
    login: str
    password: str

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

class QdrantConfig(BaseModel):
    host: str = "localhost"
    port: int = 6333

class Settings(BaseModel):
    ya_gpt: YaGPTConfig
    logging: LoggingConfig
    qdrant: QdrantConfig = QdrantConfig()

    @classmethod
    def load(cls, path: str = None) -> "Settings":
        if path is None:
            # Используем путь относительно текущего модуля
            path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        # Если в конфиге нет qdrant, добавляем его с дефолтными значениями
        if "qdrant" not in data:
            data["qdrant"] = {"host": "localhost", "port": 6333}
            
        return cls(**data)

settings = Settings.load()
