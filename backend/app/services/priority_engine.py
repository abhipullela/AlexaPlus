"""Deterministic priority engine.

Pure logic: it takes tasks in, gives scores out. No database, no web code, no AI.
Because of that it is easy to test, and the future AI agent can call it as a tool.

Score (0-100) = urgency + importance + effort + progress points, where the
maximum points each factor can give are the W_* weights below (they add to 100).
"""
from dataclasses import dataclass
from datetime import datetime

from backend.app.models.task import Priority, Status, Task

# ---- Design choices (deadline-driven). Change these numbers to retune. ----
W_URGENCY = 50      # how close the deadline is
W_IMPORTANCE = 25   # the priority label you set
W_EFFORT = 15       # how much work is still left
W_PROGRESS = 10     # bonus for tasks you've already started

IMPORTANCE = {Priority.low: 0.2, Priority.medium: 0.6, Priority.high: 1.0}
NO_DEADLINE_URGENCY = 0.1    # tasks without a deadline are rarely urgent
MAX_EFFORT_MINUTES = 8 * 60  # 8+ hours of remaining work counts as "maximum effort"


@dataclass
class ScoredTask:
    task: Task
    score: float
    overdue: bool
    breakdown: dict[str, float]  # points contributed by each factor


def score_task(task: Task, now: datetime) -> ScoredTask:
    overdue = False
    if task.deadline is None:
        urgency = NO_DEADLINE_URGENCY
    else:
        days_left = (task.deadline - now).total_seconds() / 86400
        if days_left <= 0:
            overdue = True
            urgency = 1.0
        else:
            # 0 days left -> 1.0, 1 day -> 0.5, 3 days -> 0.25, 7 days -> 0.125 ...
            urgency = 1 / (1 + days_left)

    importance = IMPORTANCE[task.priority]

    remaining_minutes = task.estimated_minutes * (1 - task.progress / 100)
    effort = min(remaining_minutes / MAX_EFFORT_MINUTES, 1.0)

    progress = task.progress / 100

    breakdown = {
        "urgency": round(urgency * W_URGENCY, 1),
        "importance": round(importance * W_IMPORTANCE, 1),
        "effort": round(effort * W_EFFORT, 1),
        "progress": round(progress * W_PROGRESS, 1),
    }
    score = round(sum(breakdown.values()), 1)
    return ScoredTask(task=task, score=score, overdue=overdue, breakdown=breakdown)


def rank_tasks(tasks: list[Task], now: datetime | None = None) -> list[ScoredTask]:
    """Score every unfinished task. Overdue tasks first, then highest score first."""
    now = now or datetime.now()
    scored = [score_task(t, now) for t in tasks if t.status != Status.done]
    scored.sort(key=lambda s: (not s.overdue, -s.score))
    return scored
