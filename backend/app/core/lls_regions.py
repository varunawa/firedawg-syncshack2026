"""Resolve an NSW postcode to a Local Land Services (LLS) region.

The region names returned here match the ``region`` column in
``data/MASTER_CROP.csv`` exactly, so the benchmark lookup can join on them.

Strategy, most trustworthy first:
1. Hand-curated postcode ranges (``LLS_POSTCODE_RANGES``).
2. The pre-built ``backend/postcode_lls_map.json`` lookup, if present.
3. Give up and return ``None`` -- the caller then falls back to the
   NSW state-wide benchmark rather than guessing a region.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_POSTCODE_MAP_PATH = _BACKEND_DIR / "postcode_lls_map.json"

# slug -> the exact spelling used in MASTER_CROP.csv
_SLUG_TO_REGION = {
    "central_tablelands": "Central Tablelands",
    "central_west": "Central West",
    "greater_sydney": "Greater Sydney",
    "hunter": "Hunter",
    "murray": "Murray",
    "north_coast": "North Coast",
    "north_west_nsw": "North West NSW",
    "northern_tablelands": "Northern Tablelands",
    "riverina": "Riverina",
    "south_east_nsw": "South East NSW",
    "western": "Western",
}

# (low, high, slug) inclusive postcode ranges. Curated for NSW LLS boundaries;
# extends the matrix from scripts/build_lls_postcode_map.py with the major
# irrigation towns the map's keyword fallback missed (e.g. Griffith 2680).
LLS_POSTCODE_RANGES: list[tuple[int, int, str]] = [
    # Murray
    (2640, 2649, "murray"), (2710, 2714, "murray"), (2731, 2739, "murray"),
    # Riverina (incl. Griffith 2680 / Leeton / Narrandera / Hay)
    (2650, 2652, "riverina"), (2653, 2666, "riverina"), (2668, 2681, "riverina"),
    (2700, 2709, "riverina"), (2715, 2717, "riverina"),
    # Central West
    (2790, 2810, "central_west"), (2820, 2825, "central_west"),
    (2827, 2836, "central_west"), (2840, 2846, "central_west"),
    (2864, 2878, "central_west"),
    # North West NSW
    (2380, 2412, "north_west_nsw"), (2831, 2839, "north_west_nsw"),
    # Northern Tablelands
    (2350, 2372, "northern_tablelands"),
    # Western
    (2825, 2826, "western"), (2879, 2898, "western"),
    # South East NSW (incl. ACT)
    (200, 299, "south_east_nsw"), (2540, 2551, "south_east_nsw"),
    (2580, 2582, "south_east_nsw"), (2600, 2639, "south_east_nsw"),
    (2900, 2920, "south_east_nsw"),
    # Hunter
    (2250, 2340, "hunter"),
    # North Coast
    (2415, 2490, "north_coast"),
    # Greater Sydney
    (2000, 2249, "greater_sydney"), (2555, 2574, "greater_sydney"),
    (2745, 2786, "greater_sydney"),
]


def _normalise_postcode(postcode: str | int | None) -> str | None:
    if postcode is None:
        return None
    digits = "".join(ch for ch in str(postcode) if ch.isdigit())
    if not digits:
        return None
    return digits.zfill(4)[:4]


@lru_cache(maxsize=1)
def _postcode_map() -> dict[str, str]:
    """postcode -> LLS region name, from the pre-built JSON (best effort)."""
    if not _POSTCODE_MAP_PATH.exists():
        return {}
    try:
        rows = json.loads(_POSTCODE_MAP_PATH.read_text() or "[]")
    except (json.JSONDecodeError, OSError):
        return {}

    out: dict[str, str] = {}
    for row in rows:
        pc = _normalise_postcode(row.get("postcode"))
        slug = row.get("lls_region_id")
        region = _SLUG_TO_REGION.get(slug)
        if pc and region and pc not in out:
            out[pc] = region
    return out


def _range_lookup(postcode: str) -> str | None:
    code = int(postcode)
    for low, high, slug in LLS_POSTCODE_RANGES:
        if low <= code <= high:
            return _SLUG_TO_REGION[slug]
    return None


def resolve_lls_region(postcode: str | int | None) -> str | None:
    """Return the LLS region name for a postcode, or ``None`` if unknown.

    The name matches the ``region`` column in MASTER_CROP.csv.
    """
    pc = _normalise_postcode(postcode)
    if pc is None:
        return None
    return _range_lookup(pc) or _postcode_map().get(pc)
