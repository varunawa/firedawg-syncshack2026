import pytest

from app.core.benchmark import (
    compare,
    crop_distribution,
    regional_benchmark,
    z_score,
)
from app.core.lls_regions import resolve_lls_region


def test_griffith_postcode_resolves_to_riverina():
    assert resolve_lls_region("2680") == "Riverina"
    assert resolve_lls_region(2680) == "Riverina"


def test_unknown_postcode_returns_none():
    assert resolve_lls_region("9999") is None
    assert resolve_lls_region("") is None
    assert resolve_lls_region(None) is None


def test_data_loader_reads_actual_postcode_lls_schema():
    from app.services.data_loader import RiskDataStore

    store = RiskDataStore()
    assert store.lookup_lls("2680", "GRIFFITH") is not None
    assert store.lookup_lls("2680", "GRIFFITH")["region_id"] == "riverina"
    assert store.lookup_crop_stats("riverina", "Cotton") is not None
    assert store.lookup_crop_stats("Riverina", "Cotton") is not None


def test_regional_benchmark_matches_region_and_crop():
    b = regional_benchmark("Riverina", "Cotton")
    assert b.region_used == "Riverina"
    assert b.is_state_fallback is False
    assert b.water_intensity_ml_per_ha == pytest.approx(9.938, abs=0.01)


def test_benchmark_falls_back_to_state_when_region_has_no_data():
    # Greater Sydney has no Rice figures -> NSW state-wide fallback.
    b = regional_benchmark("Greater Sydney", "Rice")
    assert b.is_state_fallback is True
    assert b.region_used == "New South Wales"
    assert b.water_intensity_ml_per_ha is not None


def test_benchmark_falls_back_when_region_unknown():
    b = regional_benchmark(None, "Cotton")
    assert b.is_state_fallback is True
    assert b.region_used == "New South Wales"


def test_z_score_needs_two_points():
    assert z_score(5.0, [3.0]) is None
    zs = z_score(5.0, [1.0, 5.0, 9.0])
    assert zs.sample_size == 3
    assert zs.mean == pytest.approx(5.0)
    assert zs.z == pytest.approx(0.0)


def test_single_benchmark_point_is_treated_as_neutral():
    from app.services.risk import bucket_risk, compute_z_score

    assert compute_z_score(5.0, 3.0, float("nan")) is None
    assert bucket_risk(None) == "low"


def test_single_point_benchmark_is_serializable():
    from app.services.data_loader import RiskDataStore

    stats = RiskDataStore().lookup_crop_stats("riverina", "Cotton")
    assert stats is not None
    assert stats["n"] == 1
    assert stats["std"] is None


def test_crop_distribution_is_non_trivial():
    dist = crop_distribution("Cotton")
    assert len(dist) >= 5
    assert all(v > 0 for v in dist)


def test_compare_efficient_farm_gets_low_rating():
    # 500 ML over 400 ha = 1.25 ML/ha, well below cotton benchmarks.
    c = compare(
        postcode="2680",
        lls_region=None,
        crop_category="Cotton",
        water_used_ml=500,
        land_area_ha=400,
    )
    assert c.lls_region == "Riverina"
    assert c.user_water_intensity_ml_per_ha == pytest.approx(1.25)
    assert c.delta_pct < 0
    assert c.z_score < 0
    assert c.rating == "efficient"


def test_compare_high_use_farm_gets_high_rating():
    c = compare(
        postcode="2680",
        lls_region=None,
        crop_category="Cotton",
        water_used_ml=5000,
        land_area_ha=300,
    )
    assert c.z_score > 0
    assert c.rating == "high water use"


def test_compare_rejects_zero_land_area():
    with pytest.raises(ValueError):
        compare(
            postcode="2680",
            lls_region=None,
            crop_category="Cotton",
            water_used_ml=1000,
            land_area_ha=0,
        )


def test_analyse_endpoint_end_to_end():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.routers.analyse import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    payload = {
        "location": {"postcode": "2680", "suburb": "GRIFFITH", "state": "NSW"},
        "cropCategory": "Cotton",
        "waterUsed": 1200,
        "landArea": 250,
    }
    res = client.post("/analyse", json=payload)
    assert res.status_code == 200
    body = res.json()["benchmark"]
    assert body["lls_region"] == "Riverina"
    assert body["user_water_intensity_ml_per_ha"] == 4.8
    assert body["benchmark_water_intensity_ml_per_ha"] is not None
    assert body["rating"] in {"efficient", "typical", "high water use"}

    bad = {**payload, "landArea": 0}
    assert client.post("/analyse", json=bad).status_code == 422
