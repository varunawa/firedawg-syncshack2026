from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "water_intensity_model.joblib"
)


_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Prediction model not found at {MODEL_PATH}"
            )

        _model = joblib.load(MODEL_PATH)

    return _model


def predict_water_intensity(
    crop_category: str,
    region: str,
    water_source: str,
    irrigated_area_ha: float,
    awd_ml_per_share: float | None = None,
    carry_over_ml_per_share: float | None = None,
    cumulative_allocation_ml_per_share: float | None = None,
    total_balance_ml_per_share: float | None = None,
    storage_value: float | None = None,
):
    model = get_model()

    input_data = pd.DataFrame(
        [
            {
                "crop_category": crop_category.strip().lower(),
                "region": region.strip().lower(),
                "water_source": water_source.strip().lower(),
                "irrigated_area_ha": irrigated_area_ha,
                "awd_ml_per_share": awd_ml_per_share,
                "carry_over_ml_per_share": carry_over_ml_per_share,
                "cumulative_allocation_ml_per_share":
                    cumulative_allocation_ml_per_share,
                "total_balance_ml_per_share":
                    total_balance_ml_per_share,
                "storage_value": storage_value,
            }
        ]
    )

    predicted_intensity = float(
        model.predict(input_data)[0]
    )

    predicted_total_water_ml = (
        predicted_intensity
        * irrigated_area_ha
    )

    return {
        "predicted_water_intensity_ml_per_ha":
            round(predicted_intensity, 3),
        "predicted_total_water_ml":
            round(predicted_total_water_ml, 3),
    }