from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.db import Base


class InteractionSession(Base):
    """Represents a logical session of interaction (question/answer exchange) with a user.

    Attributes:
        id (UUID): Unique session ID, generated automatically.
        user_id (int): Foreign key referencing the user who initiated the session.
        username (str | None): Telegram username of the user at the time of session.
        first_name (str | None): First name of the user at the time of session.
        last_name (str | None): Last name of the user at the time of session.
        timestamp (datetime): Timestamp when the session was created.
        messages (list[Message]): List of messages associated with the session.
    """

    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4()
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # One-to-many relationship with Message
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Session {self.id} user={self.user_id}>"
