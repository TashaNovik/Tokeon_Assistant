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

class Settings(BaseModel):
    ya_gpt: YaGPTConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, path: str = None) -> "Settings":
        if path is None:
            # Use path relative to the current module
            path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

settings = Settings.load()
