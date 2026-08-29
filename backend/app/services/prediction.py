from pathlib import Path

import joblib
import pandas as pd


APP_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = APP_DIR / "ml" / "water_intensity_model.joblib"


VALID_CROP_CATEGORIES = {
    "cotton",
    "fruit & nuts",
    "grains & oilseeds",
    "grapes & vineyards",
    "pasture & livestock feed",
    "rice",
    "vegetables",
}

VALID_REGIONS = {
    "central tablelands",
    "central west",
    "greater sydney",
    "hunter",
    "murray",
    "new south wales",
    "north coast",
    "north west nsw",
    "northern tablelands",
    "riverina",
    "south east nsw",
    "western",
}

VALID_WATER_SOURCES = {
    "gwydir",
    "lachlan",
    "lower_darling",
    "lower_namoi",
    "macquarie",
    "murray",
    "murrumbidgee",
}


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


def normalise_text(value: str) -> str:
    return value.strip().lower()


def normalise_crop_category(value: str) -> str:
    return normalise_text(value).replace("_", " ")


def normalise_region(value: str) -> str:
    return normalise_text(value).replace("_", " ")


def normalise_water_source(value: str) -> str:
    return normalise_text(value).replace(" ", "_")


def validate_category(
    value: str,
    valid_values: set[str],
    field_name: str,
    normaliser,
) -> str:
    normalised = normaliser(value)

    if normalised not in valid_values:
        raise ValueError(
            f"Invalid {field_name}: '{value}'. "
            f"Expected one of: {sorted(valid_values)}"
        )

    return normalised


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

    crop_category = validate_category(
        crop_category,
        VALID_CROP_CATEGORIES,
        "crop_category",
        normalise_crop_category,
    )

    region = validate_category(
        region,
        VALID_REGIONS,
        "region",
        normalise_region,
    )

    water_source = validate_category(
        water_source,
        VALID_WATER_SOURCES,
        "water_source",
        normalise_water_source,
    )

    input_data = pd.DataFrame(
        [
            {
                "crop_category": crop_category,
                "region": region,
                "water_source": water_source,
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