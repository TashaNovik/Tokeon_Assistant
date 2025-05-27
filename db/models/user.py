from sqlalchemy import BigInteger, Column, String
from db.db import Base


class User(Base):
    """Represents a Telegram user snapshot stored in the database.

    Attributes:
        user_id (int): The Telegram user ID (primary key).
        username (str | None): The Telegram username (optional).
        first_name (str | None): The user's first name (optional).
        last_name (str | None): The user's last name (optional).
    """

    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)  # Real Telegram user ID
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User(id={self.user_id}, uname={self.username})>"
