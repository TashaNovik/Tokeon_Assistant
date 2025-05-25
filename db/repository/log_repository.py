from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.session import InteractionSession
from db.models.message import Message
from db.repository.user_repository import UserRepository


class LogRepository:
    """Handles logging of user interactions as messages within a session."""

    @staticmethod
    def add_log(
        session: Session,
        user_id: int,
        question: str,
        answer: str,
        *,
        username=None,
        first_name=None,
        last_name=None
    ) -> InteractionSession:
        """Adds a log entry for a user interaction using a synchronous session.

        Args:
            session (Session): SQLAlchemy synchronous session.
            user_id (int): ID of the user.
            question (str): The question from the user.
            answer (str): The response from the assistant.
            username (str, optional): Telegram username of the user.
            first_name (str, optional): First name of the user.
            last_name (str, optional): Last name of the user.

        Returns:
            InteractionSession: The created interaction session containing the messages.
        """
        UserRepository.get_or_create_user(
            session,
            user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        s = InteractionSession(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(s)
        session.flush()
        session.add_all([
            Message(session_id=s.id, role="user", content=question),
            Message(session_id=s.id, role="assistant", content=answer),
        ])
        session.commit()
        session.refresh(s)
        return s

    @staticmethod
    async def add_log_async(
        session: AsyncSession,
        user_id: int,
        question: str,
        answer: str,
        *,
        username=None,
        first_name=None,
        last_name=None
    ) -> InteractionSession:
        """Adds a log entry for a user interaction using an asynchronous session.

        Args:
            session (AsyncSession): SQLAlchemy asynchronous session.
            user_id (int): ID of the user.
            question (str): The question from the user.
            answer (str): The response from the assistant.
            username (str, optional): Telegram username of the user.
            first_name (str, optional): First name of the user.
            last_name (str, optional): Last name of the user.

        Returns:
            InteractionSession: The created interaction session containing the messages.
        """
        await UserRepository.get_or_create_user_async(
            session,
            user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        s = InteractionSession(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(s)
        await session.flush()
        session.add_all([
            Message(session_id=s.id, role="user", content=question),
            Message(session_id=s.id, role="assistant", content=answer),
        ])
        await session.commit()
        await session.refresh(s)
        return s
