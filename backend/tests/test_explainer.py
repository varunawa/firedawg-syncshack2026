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
