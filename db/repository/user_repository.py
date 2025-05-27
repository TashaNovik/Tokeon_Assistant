from __future__ import annotations
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User


def _update(obj: User, **kw: Any) -> None:
    """Updates fields of a User object with non-None values.

    Args:
        obj (User): The User object to update.
        **kw (Any): Fields and their new values to set on the object.
    """
    for k, v in kw.items():
        if v is not None and getattr(obj, k) != v:
            setattr(obj, k, v)


class UserRepository:
    """Handles creation and updating of User records."""

    @staticmethod
    def get_or_create_user(
        session: Session,
        user_id: int,
        *,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Gets an existing user by ID or creates a new one (synchronously).

        Args:
            session (Session): SQLAlchemy synchronous session.
            user_id (int): Telegram user ID.
            username (Optional[str], optional): Telegram username.
            first_name (Optional[str], optional): First name.
            last_name (Optional[str], optional): Last name.

        Returns:
            User: The retrieved or newly created User object.
        """
        user: Optional[User] = session.get(User, user_id)
        if user is None:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.flush()
        else:
            _update(user, username=username, first_name=first_name, last_name=last_name)
        return user

    @staticmethod
    async def get_or_create_user_async(
        session: AsyncSession,
        user_id: int,
        *,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Gets an existing user by ID or creates a new one (asynchronously).

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session.
            user_id (int): Telegram user ID.
            username (Optional[str], optional): Telegram username.
            first_name (Optional[str], optional): First name.
            last_name (Optional[str], optional): Last name.

        Returns:
            User: The retrieved or newly created User object.
        """
        user: Optional[User] = await session.get(User, user_id)
        if user is None:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.flush()
        else:
            _update(user, username=username, first_name=first_name, last_name=last_name)
        return user
