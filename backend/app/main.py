from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.routers import tasks
from app.routers import prediction


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Hackathon convenience: create tables from models on startup.
    # Swap for Alembic migrations if the schema starts changing frequently.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="syncshack-2026 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(prediction.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
