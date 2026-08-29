"""SQLAlchemy ORM models = your database tables.

Replace `Task` with your real domain. After changing a model, restart the
server; tables are (re)created on startup (see app/main.py). Existing columns
are NOT altered automatically — drop the table in Supabase or add Alembic if
the schema starts changing a lot.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
