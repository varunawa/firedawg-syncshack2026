from pathlib import Path
import pandas as pd
from app.ml.preprocessing import get_clean_datasets

PROJECT_ROOT = Path(__file__).resolve().parents[3]

output_path = PROJECT_ROOT / "data" / "model_training.csv"


LLS_REGION_TO_VALLEY = {
    "central_tablelands": "lachlan",
    "central_west": "macquarie",
    "greater_sydney": "murray",
    "hunter": "murray",
    "murray": "murray",
    "north_coast": "murray",
    "north_west_nsw": "lower_namoi",
    "northern_tablelands": "gwydir",
    "riverina": "murrumbidgee",
    "south_east_nsw": "murray",
    "western": "lower_darling",
}


def aggregate_allocation_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse multiple AWD announcements into one row per water source.

    For the MVP we use the most recent available record for each source.
    """

    df = df.copy()

    df = df.sort_values("date")

    latest = (
        df.groupby("water_source", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return latest[
        [
            "water_source",
            "awd_ml_per_share",
            "carry_over_ml_per_share",
            "cumulative_allocation_ml_per_share",
            "total_balance_ml_per_share",
        ]
    ]


def prepare_crop_regions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert region names into the same format used by our
    water-source mapping.
    """

    df = df.copy()

    df["region_key"] = (
        df["region"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    df["water_source"] = df["region_key"].map(
        LLS_REGION_TO_VALLEY
    )

    return df


def prepare_storage_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce storage data to a single representative storage value.

    We will improve this later once we know the exact storage columns.
    """

    df = df.copy()

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    if not numeric_columns:
        return pd.DataFrame(
            {"storage_value": [None]}
        )

    storage_column = numeric_columns[-1]

    storage_value = df[storage_column].dropna()

    if storage_value.empty:
        value = None
    else:
        value = storage_value.iloc[-1]

    return pd.DataFrame({
        "storage_value": [value]
    })


def build_model_dataset():
    datasets = get_clean_datasets()

    crop = prepare_crop_regions(
        datasets["crop"]
    )

    allocation = aggregate_allocation_data(
        datasets["allocation"]
    )

    storage = prepare_storage_data(
        datasets["storage"]
    )

    model_df = crop.merge(
        allocation,
        on="water_source",
        how="left",
    )

    # MVP: same representative storage value for all observations
    model_df["storage_value"] = (
        storage["storage_value"].iloc[0]
    )

    model_df.to_csv(output_path, index=False)

    return model_df