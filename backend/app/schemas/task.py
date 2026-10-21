"""Pydantic schemas: the shape of data going IN and OUT of the API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.task import Priority, Status


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    deadline: datetime | None = None
    priority: Priority = Priority.medium
    estimated_minutes: int = Field(default=60, gt=0)


class TaskUpdate(BaseModel):
    """Every field is optional so a client can change just one thing."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    deadline: datetime | None = None
    priority: Priority | None = None
    estimated_minutes: int | None = Field(default=None, gt=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    status: Status | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets Pydantic read a DB object

    id: int
    title: str
    deadline: datetime | None
    priority: Priority
    estimated_minutes: int
    progress: int
    status: Status
    created_at: datetime


class ScoreBreakdown(BaseModel):
    """Points each factor contributed to the score."""
    urgency: float
    importance: float
    effort: float
    progress: float


class PrioritizedTask(BaseModel):
    task: TaskRead
    score: float
    overdue: bool
    breakdown: ScoreBreakdown
