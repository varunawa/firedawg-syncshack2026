"""/analyse -- benchmark a farm's water use against the NSW crop dataset."""

from fastapi import APIRouter, HTTPException

from app.core.benchmark import compare
from app.schemas import AnalyseIn, AnalyseOut, BenchmarkResult

router = APIRouter()


@router.post("/analyse", response_model=AnalyseOut, tags=["analyse"])
def analyse_business(data: AnalyseIn) -> AnalyseOut:
    try:
        result = compare(
            postcode=data.location.postcode,
            lls_region=None,
            crop_category=data.cropCategory,
            water_used_ml=data.waterUsed,
            land_area_ha=data.landArea,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AnalyseOut(
        success=True,
        benchmark=BenchmarkResult(**vars(result)),
    )
