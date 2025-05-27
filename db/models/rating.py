from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.db import Base


class Rating(Base):
    """Represents a user's rating of a message.

    Attributes:
        id (int): Primary key.
        user_id (int): ID of the user who submitted the rating.
        message_id (int): ID of the rated message.
        rating_type (str): Type of rating ('positive', 'neutral', 'negative').
        timestamp (datetime): When the rating was created.
        message (Message): Related message object.
        comment (Comment | None): Optional comment attached to the rating.
    """

    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)

    rating_type = Column(String(20), nullable=False)  # 'positive' | 'neutral' | 'negative'
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="ratings", lazy="joined")
    comment = relationship("Comment", back_populates="rating", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Rating {self.id} msg={self.message_id} {self.rating_type}>"
