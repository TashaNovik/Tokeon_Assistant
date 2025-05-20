import yaml
from pydantic import BaseModel

class TelegramConfig(BaseModel):
    """Telegram bot configuration.

        Attributes:
            token: Telegram bot token.
            webhook_path: Webhook URL path for receiving updates.
        """
    token: str
    webhook_path: str

class LoggingConfig(BaseModel):
    """Logging configuration.

        Attributes:
            level: Logging level (default is "INFO").
            format: Logging message format.
        """
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"

class Settings(BaseModel):
    """Application settings containing Telegram and logging configurations.

        Attributes:
            telegram: TelegramConfig instance.
            logging: LoggingConfig instance.
        """
    telegram: TelegramConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, path: str = "telegram_bot/config.yaml") -> "Settings":
        """Load settings from a YAML configuration file.

                Args:
                    path: Path to the YAML config file.

                Returns:
                    An instance of Settings populated with data from the file.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

settings = Settings.load()
