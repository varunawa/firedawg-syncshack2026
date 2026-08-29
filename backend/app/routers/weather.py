from fastapi import APIRouter, HTTPException
from app.services.weather import get_weather_for_location

router = APIRouter()


@router.get("/weather")
async def get_weather(location: str):
    try:
        return await get_weather_for_location(location)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:
        print("Weather error:", e)

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve weather data"
        )