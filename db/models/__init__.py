"""Imports all ORM models to ensure SQLAlchemy metadata registration.

This module ensures that all models are registered with the `Base` metadata
so they can be discovered during database initialization, migrations, or reflection.
"""

from db.db import Base  # noqa: F401
from db.models.user import User  # noqa: F401
from db.models.session import InteractionSession  # noqa: F401
from db.models.message import Message  # noqa: F401
from db.models.rating import Rating  # noqa: F401
from db.models.comment import Comment  # noqa: F401
