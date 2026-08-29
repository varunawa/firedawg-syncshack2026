from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
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


def create_preprocessor():
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

    return ColumnTransformer(
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


def evaluate_model(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5

    print(f"\n{name}")
    print("-" * len(name))
    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))

    return {
        "name": name,
        "model": model,
        "mae": mae,
        "rmse": rmse,
    }


def compare_models():
    df = build_model_dataset()

    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES

    df = df.dropna(subset=[TARGET]).copy()

    X = df[feature_columns]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    print("Total rows:", len(df))
    print("Training rows:", len(X_train))
    print("Test rows:", len(X_test))

    linear_model = Pipeline(
        steps=[
            ("preprocessor", create_preprocessor()),
            ("regressor", LinearRegression()),
        ]
    )

    random_forest_model = Pipeline(
        steps=[
            ("preprocessor", create_preprocessor()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=200,
                    random_state=42,
                ),
            ),
        ]
    )

    results = []

    results.append(
        evaluate_model(
            "Linear Regression",
            linear_model,
            X_train,
            X_test,
            y_train,
            y_test,
        )
    )

    results.append(
        evaluate_model(
            "Random Forest",
            random_forest_model,
            X_train,
            X_test,
            y_train,
            y_test,
        )
    )

    best = min(
        results,
        key=lambda result: result["rmse"],
    )

    print("\nBest model:", best["name"])
    print("Best RMSE:", round(best["rmse"], 4))

    joblib.dump(
        best["model"],
        MODEL_PATH,
    )

    print("Saved best model to:", MODEL_PATH)

    return results


if __name__ == "__main__":
    compare_models()