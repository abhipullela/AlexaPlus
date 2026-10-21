from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.models.task import Priority, Status, Task
from backend.app.services.priority_engine import rank_tasks, score_task
from backend.tests.test_tasks import client, setup_function  # noqa: F401  (reuse test DB)

NOW = datetime(2026, 9, 10, 12, 0)


def make(title, days=None, priority=Priority.medium, minutes=60, progress=0, status=Status.pending):
    deadline = None if days is None else NOW + timedelta(days=days)
    return Task(title=title, deadline=deadline, priority=priority,
                estimated_minutes=minutes, progress=progress, status=status)


def test_closer_deadline_scores_higher():
    assert score_task(make("a", days=1), NOW).score > score_task(make("b", days=5), NOW).score


def test_higher_priority_scores_higher_when_all_else_equal():
    hi = score_task(make("a", days=3, priority=Priority.high), NOW).score
    lo = score_task(make("b", days=3, priority=Priority.low), NOW).score
    assert hi > lo


def test_score_always_between_0_and_100():
    extremes = [make("x", days=-30, priority=Priority.high, minutes=9999),
                make("y", days=500, priority=Priority.low, minutes=1)]
    for t in extremes:
        assert 0 <= score_task(t, NOW).score <= 100


def test_overdue_is_flagged_and_pinned_to_top():
    overdue_low = make("late", days=-1, priority=Priority.low, minutes=10)
    urgent_high = make("urgent", days=0.1, priority=Priority.high, minutes=480)
    ranked = rank_tasks([urgent_high, overdue_low], NOW)
    assert ranked[0].task.title == "late" and ranked[0].overdue
    assert not ranked[1].overdue


def test_done_tasks_are_excluded():
    ranked = rank_tasks([make("a", days=1), make("b", days=1, status=Status.done)], NOW)
    assert [s.task.title for s in ranked] == ["a"]


def test_no_deadline_ranks_below_deadline_task():
    ranked = rank_tasks([make("none"), make("soon", days=2)], NOW)
    assert ranked[0].task.title == "soon"


def test_prioritized_endpoint():
    soon = (datetime.now() + timedelta(days=1)).isoformat()
    late = (datetime.now() - timedelta(days=1)).isoformat()
    client.post("/tasks", json={"title": "Soon", "deadline": soon, "priority": "high"})
    client.post("/tasks", json={"title": "Late", "deadline": late, "priority": "low"})
    done = client.post("/tasks", json={"title": "Done"}).json()["id"]
    client.patch(f"/tasks/{done}", json={"progress": 100})

    r = client.get("/tasks/prioritized")
    assert r.status_code == 200
    body = r.json()
    assert [b["task"]["title"] for b in body] == ["Late", "Soon"]
    assert body[0]["overdue"] is True
    assert set(body[0]["breakdown"]) == {"urgency", "importance", "effort", "progress"}
