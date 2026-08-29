from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"


def load_crop_data():
    path = DATA_DIR / "MASTER_CROP.csv"
    return pd.read_csv(path)


def load_water_allocation_data():
    path = DATA_DIR / "water_allocation.csv"
    return pd.read_csv(path)


def load_storage_data():
    path = DATA_DIR / "warragamba_storage.csv"
    return pd.read_csv(path)


def load_all_datasets():
    return {
        "crop": load_crop_data(),
        "allocation": load_water_allocation_data(),
        "storage": load_storage_data(),
    }