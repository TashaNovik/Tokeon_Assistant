from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.db import Base


class Comment(Base):
    """Represents a user-written comment associated with a rating.

    Attributes:
        rating_id (int): Primary key and foreign key linking to the associated rating.
        content (str): Text content of the comment.
        timestamp (datetime): When the comment was created.
        rating (Rating): The associated Rating object (one-to-one relationship).
    """

    __tablename__ = "comments"

    rating_id = Column(
        Integer,
        ForeignKey("ratings.id", ondelete="CASCADE"),
        primary_key=True
    )
    content = Column(Text, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    rating = relationship(
        "Rating",
        back_populates="comment",
        uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Comment rating={self.rating_id}>"
