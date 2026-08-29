from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LocationData(BaseModel):
    postcode: str | int
    suburb: str
    state: str
    region_id: str
    valleyname: str


class BusinessData(BaseModel):
    location: LocationData
    cropCategory: str
    waterUsed: float
    landArea: float


@router.post("/analyse")
def analyse_business(data: BusinessData):
    print("\n===== RECEIVED FROM FRONTEND =====")
    print(data.model_dump())
    print("==================================\n")

    return {
        "success": True,
        "received": data.model_dump(),
    }