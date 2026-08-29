from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.prediction import predict_water_intensity


router = APIRouter()


class PredictionRequest(BaseModel):
    crop_category: str
    region: str
    water_source: str

    irrigated_area_ha: float = Field(gt=0)

    awd_ml_per_share: float | None = None
    carry_over_ml_per_share: float | None = None
    cumulative_allocation_ml_per_share: float | None = None
    total_balance_ml_per_share: float | None = None
    storage_value: float | None = None


@router.post("/prediction")
async def make_prediction(
    request: PredictionRequest,
):
    try:
        prediction = predict_water_intensity(
            crop_category=request.crop_category,
            region=request.region,
            water_source=request.water_source,
            irrigated_area_ha=request.irrigated_area_ha,
            awd_ml_per_share=request.awd_ml_per_share,
            carry_over_ml_per_share=
                request.carry_over_ml_per_share,
            cumulative_allocation_ml_per_share=
                request.cumulative_allocation_ml_per_share,
            total_balance_ml_per_share=
                request.total_balance_ml_per_share,
            storage_value=request.storage_value,
        )

        return {
            "success": True,
            **prediction,
        }

    except Exception as e:
        print("Prediction error:", e)

        raise HTTPException(
            status_code=500,
            detail="Unable to generate prediction",
        )