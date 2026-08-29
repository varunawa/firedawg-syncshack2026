import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# -----------------------------
# Project paths
# -----------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


# -----------------------------
# Credentials
# -----------------------------

API_KEY = os.getenv("WATERNSW_API_KEY")
API_SECRET = os.getenv("WATERNSW_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError(
        "WaterNSW credentials missing from backend/.env"
    )


# -----------------------------
# Warragamba settings
# -----------------------------

DAM_ID = "212243"

FROM_DATE = "2016-08-01"
TO_DATE = "2026-08-29"

TOKEN_URL = (
    "https://api.onegov.nsw.gov.au/"
    "oauth/client_credential/accesstoken"
)

RESOURCE_URL = (
    "https://api.onegov.nsw.gov.au/"
    f"waternsw-waterinsights/v1/dams/{DAM_ID}/resources"
)


# -----------------------------
# Step 1: Get access token
# -----------------------------

print("Getting access token...")

token_response = requests.get(
    TOKEN_URL,
    params={
        "grant_type": "client_credentials"
    },
    auth=(API_KEY, API_SECRET),
    timeout=30
)

token_response.raise_for_status()

access_token = token_response.json()["access_token"]

print("Access token received.")


# -----------------------------
# Step 2: Get 10 years of data
# -----------------------------

print("Downloading Warragamba data...")

response = requests.get(
    RESOURCE_URL,
    headers={
        "Authorization": f"Bearer {access_token}",
        "apikey": API_KEY
    },
    params={
        "from": FROM_DATE,
        "to": TO_DATE
    },
    timeout=30
)

response.raise_for_status()

data = response.json()


# -----------------------------
# Step 3: Look at API structure
# -----------------------------

data = response.json()

# Get Warragamba's monthly records
dam = data["dams"][0]
resources = dam["resources"]

# Convert to a pandas DataFrame
df = pd.DataFrame(resources)

# Add dam information
df.insert(0, "dam_id", dam["dam_id"])
df.insert(1, "dam_name", dam["dam_name"])

# Convert date into proper date format
df["date"] = pd.to_datetime(df["date"])

# API gives newest first, so sort oldest -> newest
df = df.sort_values("date")

# Create the data folder if it doesn't exist
data_folder = PROJECT_ROOT / "data"
data_folder.mkdir(exist_ok=True)

# File location
output_file = data_folder / "warragamba_storage.csv"

# Save CSV
df.to_csv(output_file, index=False)

print(f"Successfully saved {len(df)} records!")
print(f"CSV saved to: {output_file}")

print()
print(df.head())
print()
print(df.tail())