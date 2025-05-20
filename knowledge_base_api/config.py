import yaml
from pydantic import BaseModel

class YaGPTConfig(BaseModel):
    """
    Configuration for the YaGPT API.

    Attributes:
        api_key (str): API key for accessing the service.
        folder_id (str): Folder ID in the service.
        login (str): User login.
        password (str): User password.
    """
    api_key: str
    folder_id: str
    login: str
    password: str

class LoggingConfig(BaseModel):
    """
    Configuration for logging.

    Attributes:
        level (str): Logging level. Default is "INFO".
        format (str): Format of log messages.
    """
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

class Settings(BaseModel):
    """
    Main application configuration combining YaGPT and logging settings.

    Attributes:
        ya_gpt (YaGPTConfig): YaGPT API configuration.
        logging (LoggingConfig): Logging configuration.
    """

    ya_gpt: YaGPTConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, path: str = "tokeon_assistant_rest_api/config.yaml") -> "Settings":
        """
        Loads configuration from a YAML file.

        Args:
            path (str): Path to the YAML configuration file.

        Returns:
            Settings: Instance of the configuration loaded from the file.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

settings = Settings.load()

