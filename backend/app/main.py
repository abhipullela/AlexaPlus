"""App entry point. Run from the repo root with:
    uvicorn backend.app.main:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app import models  # noqa: F401  (importing registers the tables)
from backend.app.api import tasks
from backend.app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)   # make sure the DB folder exists
    Base.metadata.create_all(engine)     # create tables if they don't exist yet
    yield


app = FastAPI(title="Alexa+ Student Productivity Agent", lifespan=lifespan)
app.include_router(tasks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
