"""The Task database table."""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=60)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100 (%)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
