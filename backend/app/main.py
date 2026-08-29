# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.config import settings
# from app.db import Base, engine
# from app.routers import tasks, analyse


# @asynccontextmanager
# async def lifespan(_: FastAPI):
#     Base.metadata.create_all(bind=engine)
#     yield


# app = FastAPI(
#     title="syncshack-2026 API",
#     lifespan=lifespan
# )


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# app.include_router(tasks.router)
# app.include_router(analyse.router)


# @app.get("/health", tags=["meta"])
# def health():
#     return {"status": "ok"}

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.routers import tasks
from app.routers.analyse import router as analyse_router
from app.routers.weather import router as weather_router
from app.routers.waternsw import router as waternsw_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="syncshack-2026 API",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)

# NB: the Vite dev proxy rewrites "/api/*" -> "/*", so the frontend's
# POST /api/analyse reaches the backend as /analyse (no prefix here).
app.include_router(analyse_router, tags=["analyse"])

app.include_router(
    weather_router,
    prefix="/api",
    tags=["weather"],
)


app.include_router(
    waternsw_router,
    prefix="/api/water",
    tags=["WaterNSW"],
)

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}