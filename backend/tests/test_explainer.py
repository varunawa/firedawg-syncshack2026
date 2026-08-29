import json
from unittest.mock import AsyncMock

import pytest

from app.core.benchmark import compare
from app.services import explainer


@pytest.fixture
def comparison():
    return compare(
        postcode="2680",
        lls_region=None,
        crop_category="Cotton",
        water_used_ml=1200,
        land_area_ha=250,
    )


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return _FakeResponse(self._text)


class _FakeClient:
    def __init__(self, text=None, error=None):
        self.models = _FakeModels(text, error)


def test_returns_none_without_api_key(monkeypatch, comparison):
    monkeypatch.setattr(explainer, "_get_client", lambda: None)
    assert explainer.explain_comparison(comparison) is None


def test_returns_text_from_llm(monkeypatch, comparison):
    fake = _FakeClient(text="Your farm uses about half the regional benchmark.")
    monkeypatch.setattr(explainer, "_get_client", lambda: fake)

    out = explainer.explain_comparison(comparison)

    assert out == "Your farm uses about half the regional benchmark."
    assert fake.models.calls[0]["model"]  # a model was passed


def test_swallows_api_errors(monkeypatch, comparison):
    monkeypatch.setattr(
        explainer, "_get_client", lambda: _FakeClient(error=RuntimeError("boom"))
    )
    assert explainer.explain_comparison(comparison) is None


def test_endpoint_returns_null_explanation_when_unconfigured(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setattr(explainer, "_get_client", lambda: None)

    from app.routers.analyse import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    res = client.post("/analyse/explain", json={
        "location": {"postcode": "2680", "suburb": "GRIFFITH", "state": "NSW"},
        "cropCategory": "Cotton", "waterUsed": 1200, "landArea": 250,
    })

    assert res.status_code == 200
    assert res.json() == {"success": True, "explanation": None}


def test_analyse_explain_includes_environmental_stress_in_payload(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import app.routers.analyse as analyse_route

    fake = _FakeClient(text="Risk is elevated by water stress and dry conditions.")
    monkeypatch.setattr(explainer, "_get_client", lambda: fake)
    monkeypatch.setattr(analyse_route, "estimate_allocation_factor", lambda region: 1.4)
    monkeypatch.setattr(analyse_route, "estimate_rainfall_factor", lambda summary: 1.3)
    monkeypatch.setattr(analyse_route, "geocode_location", AsyncMock(return_value={"latitude": -34.0, "longitude": 146.0}))
    monkeypatch.setattr(analyse_route, "get_weather_data", AsyncMock(return_value={"summary": {"seven_day_rainfall_mm": 12.0, "climatic_water_deficit_mm": 54.0}}))

    from app.routers.analyse import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    res = client.post("/analyse/explain", json={
        "location": {"postcode": "2680", "suburb": "GRIFFITH", "state": "NSW"},
        "cropCategory": "Cotton", "waterUsed": 2000, "landArea": 250,
    })

    assert res.status_code == 200
    payload = json.loads(fake.models.calls[0]["contents"])
    assert payload["allocation_factor"] == 1.4
    assert payload["rainfall_factor"] == 1.3
