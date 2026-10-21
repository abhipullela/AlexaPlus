"""HTTP endpoints for tasks."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.task import Status
from backend.app.schemas.task import PrioritizedTask, TaskCreate, TaskRead, TaskUpdate
from backend.app.services import priority_engine, task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_or_404(db: Session, task_id: int):
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    return task_service.create_task(db, data)


@router.get("", response_model=list[TaskRead])
def list_tasks(status: Status | None = None, db: Session = Depends(get_db)):
    return task_service.list_tasks(db, status)


@router.get("/prioritized", response_model=list[PrioritizedTask])
def prioritized_tasks(db: Session = Depends(get_db)):
    """Unfinished tasks ranked by priority score (overdue tasks pinned to the top).

    NOTE: this must stay ABOVE "/{task_id}", otherwise FastAPI would treat the
    word "prioritized" as a task id.
    """
    ranked = priority_engine.rank_tasks(task_service.list_tasks(db))
    return [
        PrioritizedTask(task=s.task, score=s.score, overdue=s.overdue, breakdown=s.breakdown)
        for s in ranked
    ]


@router.get("/{task_id}", response_model=TaskRead)
def read_task(task_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    return task_service.update_task(db, _get_or_404(db, task_id), data)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task_service.delete_task(db, _get_or_404(db, task_id))
