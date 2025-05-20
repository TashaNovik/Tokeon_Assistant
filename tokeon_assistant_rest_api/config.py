import yaml
from pydantic import BaseModel

class YaGPTConfig(BaseModel):
    """
    Configuration for YaGPT API credentials.

    Attributes:
        api_key (str): API key for authentication.
        folder_id (str): Folder identifier in the YaGPT service.
        login (str): User login credential.
        password (str): User password credential.
    """
    api_key: str
    folder_id: str
    login: str
    password: str

class LoggingConfig(BaseModel):
    """
    Configuration for logging behavior.

    Attributes:
        level (str): Logging level, default is "INFO".
        format (str): Log message format string.
    """
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

class Settings(BaseModel):
    """
    Application settings combining YaGPT and logging configurations.

    Attributes:
        ya_gpt (YaGPTConfig): Configuration for YaGPT API.
        logging (LoggingConfig): Configuration for logging.

    Methods:
        load(path: str = "tokeon_assistant_rest_api/config.yaml") -> Settings:
            Loads settings from a YAML file and returns a Settings instance.
    """
    ya_gpt: YaGPTConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, path: str = "tokeon_assistant_rest_api/config.yaml") -> "Settings":
        """
        Loads settings from a YAML configuration file.

        Args:
            path (str): Path to the YAML configuration file. Defaults to "tokeon_assistant_rest_api/config.yaml".

        Returns:
            Settings: An instance of the Settings class populated with data from the YAML file.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

settings = Settings.load()
