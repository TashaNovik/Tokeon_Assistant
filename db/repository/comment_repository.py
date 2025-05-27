# === db/repository/comment_repository.py ===
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.comment import Comment
from db.models.rating import Rating


class CommentRepository:
    @staticmethod
    def add_comment(session: Session, rating_id: int, text: str) -> Comment | None:
        if session.get(Rating, rating_id) is None:
            return None
        c = Comment(rating_id=rating_id, content=text)
        session.add(c)
        session.commit()
        session.refresh(c)
        return c

    @staticmethod
    async def add_comment_async(session: AsyncSession, rating_id: int, text: str) -> Comment | None:
        if await session.get(Rating, rating_id) is None:
            return None
        c = Comment(rating_id=rating_id, content=text)
        session.add(c)
        await session.commit()
        await session.refresh(c)
        return c