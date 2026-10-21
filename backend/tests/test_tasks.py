from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models  # noqa: F401
from backend.app.database import Base, get_db
from backend.app.main import app

# A throwaway in-memory database, so tests never touch your real data.
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_task():
    r = client.post("/tasks", json={"title": "DSA Assignment", "priority": "high",
                                    "estimated_minutes": 120,
                                    "deadline": "2026-09-12T18:00:00"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "DSA Assignment" and body["status"] == "pending"
    assert client.get(f"/tasks/{body['id']}").json()["priority"] == "high"


def test_validation_rejects_bad_input():
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.post("/tasks", json={"title": "x", "estimated_minutes": 0}).status_code == 422


def test_progress_updates_status():
    tid = client.post("/tasks", json={"title": "OS Assignment"}).json()["id"]
    assert client.patch(f"/tasks/{tid}", json={"progress": 40}).json()["status"] == "in_progress"
    assert client.patch(f"/tasks/{tid}", json={"progress": 100}).json()["status"] == "done"


def test_list_filter_and_delete():
    a = client.post("/tasks", json={"title": "A"}).json()["id"]
    client.post("/tasks", json={"title": "B"})
    client.patch(f"/tasks/{a}", json={"progress": 100})
    assert len(client.get("/tasks").json()) == 2
    assert len(client.get("/tasks?status=done").json()) == 1
    assert client.delete(f"/tasks/{a}").status_code == 204
    assert client.get(f"/tasks/{a}").status_code == 404
