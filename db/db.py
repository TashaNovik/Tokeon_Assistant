import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# === Environment Configuration ===
DATABASE_URL_SYNC: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:123456789@localhost:5432/tokeon_db"
)
"""Synchronous database connection string."""

DATABASE_URL_ASYNC: str = os.getenv(
    "DATABASE_URL_ASYNC",
    "postgresql+asyncpg://postgres:123456789@localhost:5432/tokeon_db"
)
"""Asynchronous database connection string."""

# === Engine Initialization ===
engine = create_engine(DATABASE_URL_SYNC, future=True)
"""SQLAlchemy engine for synchronous operations."""

async_engine = create_async_engine(DATABASE_URL_ASYNC, future=True)
"""SQLAlchemy engine for asynchronous operations."""

# === Session Factories ===
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
"""Factory for creating synchronous SQLAlchemy sessions."""

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)
"""Factory for creating asynchronous SQLAlchemy sessions."""

# === Base Class ===
Base = declarative_base()
"""Declarative base class for ORM models."""
