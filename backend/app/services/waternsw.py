import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# Environment
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("WATERNSW_API_KEY")
API_SECRET = os.getenv("WATERNSW_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError(
        "WaterNSW credentials missing from backend/.env"
    )


# --------------------------------------------------
# WaterNSW URLs
# --------------------------------------------------

TOKEN_URL = (
    "https://api.onegov.nsw.gov.au/"
    "oauth/client_credential/accesstoken"
)

BASE_URL = (
    "https://api.onegov.nsw.gov.au/"
    "waternsw-waterinsights/v1"
)


# --------------------------------------------------
# Token cache
# --------------------------------------------------

_access_token = None
_token_expiry = 0


def get_access_token():
    global _access_token, _token_expiry

    # Reuse existing token if still valid
    if _access_token and time.time() < _token_expiry:
        return _access_token

    response = requests.get(
        TOKEN_URL,
        params={
            "grant_type": "client_credentials"
        },
        auth=(API_KEY, API_SECRET),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    _access_token = data["access_token"]

    # Token lasts approximately 12 hours.
    # Use expires_in if WaterNSW supplies it.
    expires_in = int(
        data.get("expires_in", 11 * 60 * 60)
    )

    # Refresh slightly before expiry
    _token_expiry = time.time() + expires_in - 60

    return _access_token


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "apikey": API_KEY,
    }


# --------------------------------------------------
# 1. Get ALL WaterNSW dams
# --------------------------------------------------

def get_all_dams():
    response = requests.get(
        f"{BASE_URL}/dams",
        headers=get_headers(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# 2. Get information about ONE dam
# --------------------------------------------------

def get_dam(dam_id: str):
    response = requests.get(
        f"{BASE_URL}/dams/{dam_id}",
        headers=get_headers(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# 3. Get latest/current data for ONE dam
# --------------------------------------------------

def get_latest_dam_data(dam_id: str):
    response = requests.get(
        f"{BASE_URL}/dams/{dam_id}/resources/latest",
        headers=get_headers(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# 4. Get historical data for ANY dam
# --------------------------------------------------

def get_dam_history(
    dam_id: str,
    from_date: str,
    to_date: str,
):
    response = requests.get(
        f"{BASE_URL}/dams/{dam_id}/resources",
        headers=get_headers(),
        params={
            "from": from_date,
            "to": to_date,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()