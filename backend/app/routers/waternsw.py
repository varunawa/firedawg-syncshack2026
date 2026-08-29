from fastapi import APIRouter, HTTPException

from app.services.waternsw import (
    get_all_dams,
    get_dam,
    get_latest_dam_data,
    get_dam_history,
)

router = APIRouter()


@router.get("/dams")
def all_dams():
    try:
        return get_all_dams()
    except Exception as e:
        print("WaterNSW error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve dams",
        )


@router.get("/dams/{dam_id}")
def dam_details(dam_id: str):
    try:
        return get_dam(dam_id)
    except Exception as e:
        print("WaterNSW error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve dam details",
        )


@router.get("/dams/{dam_id}/latest")
def dam_latest(dam_id: str):
    try:
        return get_latest_dam_data(dam_id)
    except Exception as e:
        print("WaterNSW error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve latest dam data",
        )


@router.get("/dams/{dam_id}/history")
def dam_history(
    dam_id: str,
    from_date: str,
    to_date: str,
):
    try:
        return get_dam_history(
            dam_id,
            from_date,
            to_date,
        )
    except Exception as e:
        print("WaterNSW error:", e)
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve dam history",
        )