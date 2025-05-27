from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.db import Base


class Message(Base):
    """Represents a single message within a dialog session.

    Attributes:
        id (int): Primary key.
        session_id (UUID): Foreign key referencing the session this message belongs to.
        role (str): Sender role, either 'user' or 'assistant'.
        content (str): Text content of the message.
        timestamp (datetime): Timestamp when the message was created.
        session (InteractionSession): The parent interaction session.
        ratings (list[Rating]): List of ratings associated with this message.
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("InteractionSession", back_populates="messages")
    ratings = relationship("Rating", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Message {self.id} role={self.role}>"
