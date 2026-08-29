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
from pydantic import BaseModel

from app.config import settings
from app.db import Base, engine
from app.routers import tasks


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


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


class LocationData(BaseModel):
    postcode: str | int
    suburb: str
    state: str
    region_id: str
    VALLEY_NAME: str


class BusinessData(BaseModel):
    location: LocationData
    cropCategory: str
    waterUsed: float
    landArea: float


@app.post("/analyse")
def analyse_business(data: BusinessData):
    print("\n===== DATA RECEIVED IN MAIN.PY =====")

    print("Full data:")
    print(data.model_dump())

    print("\nLocation:")
    print("Suburb:", data.location.suburb)
    print("Postcode:", data.location.postcode)
    print("State:", data.location.state)
    print("Region ID:", data.location.region_id)
    print("Valley:", data.location.VALLEY_NAME)

    print("\nBusiness:")
    print("Crop category:", data.cropCategory)
    print("Water used:", data.waterUsed)
    print("Land area:", data.landArea)

    print("===================================\n")

    return {
        "success": True,
        "message": "main.py received the data"
    }