"""Business logic for tasks. The API layer calls these; they talk to the database."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.task import Status, Task
from backend.app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, status: Status | None = None) -> list[Task]:
    query = select(Task).order_by(Task.deadline.is_(None), Task.deadline)
    if status is not None:
        query = query.where(Task.status == status)
    return list(db.scalars(query))


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    # exclude_unset=True -> only apply fields the client actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    # Keep progress and status consistent with each other
    if task.progress == 100:
        task.status = Status.done
    elif task.progress > 0 and task.status == Status.pending:
        task.status = Status.in_progress

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
