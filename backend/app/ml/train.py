from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.ml.build_dataset import build_model_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "backend" / "app" / "ml" / "water_intensity_model.joblib"


TARGET = "water_intensity_ml_per_ha"

CATEGORICAL_FEATURES = [
    "crop_category",
    "region",
    "water_source",
]

NUMERIC_FEATURES = [
    "irrigated_area_ha",
    "awd_ml_per_share",
    "carry_over_ml_per_share",
    "cumulative_allocation_ml_per_share",
    "total_balance_ml_per_share",
    "storage_value",
]


def train_baseline_model():
    df = build_model_dataset()

    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES

    df = df.dropna(
        subset=[TARGET]
    ).copy()

    X = df[feature_columns]
    y = df[TARGET]

    categorical_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore"),
            ),
        ]
    )

    numeric_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_transformer,
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                numeric_transformer,
                NUMERIC_FEATURES,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )

    model.fit(X, y)

    predictions = model.predict(X)

    mae = mean_absolute_error(
        y,
        predictions,
    )

    rmse = mean_squared_error(
        y,
        predictions,
    ) ** 0.5

    print("Training rows:", len(df))
    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print("Model saved to:", MODEL_PATH)

    return model


if __name__ == "__main__":
    train_baseline_model()