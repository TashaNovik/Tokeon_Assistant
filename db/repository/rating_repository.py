
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.rating import Rating


class RatingRepository:
    """Handles creation of rating entries."""

    @staticmethod
    def add_rating(
        session: Session,
        user_id: int,
        message_id: int,
        rating_type: str,
        comment: Optional[str] = None,
    ) -> Rating:
        """Creates a new rating record using a synchronous session.

        Args:
            session (Session): SQLAlchemy synchronous session.
            user_id (int): ID of the user submitting the rating.
            message_id (int): ID of the message being rated.
            rating_type (str): Type/category of the rating (e.g., 'like', 'dislike').
            comment (Optional[str], optional): Optional comment associated with the rating.

        Returns:
            Rating: The created Rating object.
        """
        rating = Rating(
            user_id=user_id,
            message_id=message_id,
            rating_type=rating_type,
            comment=comment,
        )
        session.add(rating)
        session.commit()
        session.refresh(rating)
        return rating

    @staticmethod
    async def add_rating_async(
        session: AsyncSession,
        user_id: int,
        message_id: int,
        rating_type: str,
        comment: Optional[str] = None,
    ) -> Rating:
        """Creates a new rating record using an asynchronous session.

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session.
            user_id (int): ID of the user submitting the rating.
            message_id (int): ID of the message being rated.
            rating_type (str): Type/category of the rating (e.g., 'like', 'dislike').
            comment (Optional[str], optional): Optional comment associated with the rating.

        Returns:
            Rating: The created Rating object.
        """
        rating = Rating(
            user_id=user_id,
            message_id=message_id,
            rating_type=rating_type,
            comment=comment,
        )
        session.add(rating)
        await session.commit()
        await session.refresh(rating)
        return rating
