"""/analyse -- benchmark a farm's water use against the NSW crop dataset."""

from fastapi import APIRouter, HTTPException

from app.core.benchmark import Comparison, compare
from app.schemas import AnalyseIn, AnalyseOut, BenchmarkResult, ExplainOut
from app.services.explainer import explain_comparison

router = APIRouter()


def _run_comparison(data: AnalyseIn) -> Comparison:
    try:
        return compare(
            postcode=data.location.postcode,
            lls_region=None,
            crop_category=data.cropCategory,
            water_used_ml=data.waterUsed,
            land_area_ha=data.landArea,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyse", response_model=AnalyseOut, tags=["analyse"])
def analyse_business(data: AnalyseIn) -> AnalyseOut:
    result = _run_comparison(data)
    return AnalyseOut(success=True, benchmark=BenchmarkResult(**vars(result)))


@router.post("/analyse/explain", response_model=ExplainOut, tags=["analyse"])
def explain_business(data: AnalyseIn) -> ExplainOut:
    """Plain-English summary of the benchmark result (calls Claude).

    Call this after /analyse so the stats render immediately and the summary
    fills in a moment later. Returns explanation: null if the LLM is
    unconfigured or unavailable -- never fails the request for that reason.
    """
    result = _run_comparison(data)
    return ExplainOut(success=True, explanation=explain_comparison(result))
