import pandas as pd

from app.ml.data_loader import load_all_datasets


def clean_crop_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # standardise text
    for col in ["year", "state", "region_type", "region", "crop_category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    # numeric columns
    numeric_cols = [
        "total_area_grown_ha",
        "irrigated_area_ha",
        "water_applied_ml",
        "water_intensity_ml_per_ha",
        "agricultural_businesses_estimate",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # target must exist
    df = df.dropna(subset=["water_intensity_ml_per_ha"])

    # remove impossible target values
    df = df[df["water_intensity_ml_per_ha"] >= 0]

    return df


def clean_allocation_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["water_source", "licence_category", "water_year"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            dayfirst=True,
            errors="coerce"
        )

    numeric_cols = [
        "awd_ml_per_share",
        "carry_over_ml_per_share",
        "cumulative_allocation_ml_per_share",
        "total_balance_ml_per_share",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def clean_storage_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # standardise column names first
    df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    # try to identify/convert date columns
    for col in df.columns:
        if "date" in col:
            df[col] = pd.to_datetime(
                df[col],
                dayfirst=True,
                errors="coerce"
            )

    return df


def get_clean_datasets():
    datasets = load_all_datasets()

    return {
        "crop": clean_crop_data(datasets["crop"]),
        "allocation": clean_allocation_data(datasets["allocation"]),
        "storage": clean_storage_data(datasets["storage"]),
    }