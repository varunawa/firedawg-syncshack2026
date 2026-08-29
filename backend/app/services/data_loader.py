import json
from functools import lru_cache

import pandas as pd

from app.config import settings
from app.core.lls_regions import resolve_lls_region


def _region_slug_from_name(name: str | None) -> str | None:
    if not name:
        return None
    slug = name.strip().lower().replace("/", "_")
    aliases = {
        "south east nsw": "south_east_nsw",
        "north west nsw": "north_west_nsw",
        "central tablelands": "central_tablelands",
        "central west": "central_west",
        "greater sydney": "greater_sydney",
        "hunter": "hunter",
        "murray": "murray",
        "north coast": "north_coast",
        "northern tablelands": "northern_tablelands",
        "riverina": "riverina",
        "western": "western",
    }
    return aliases.get(slug, slug.replace(" ", "_"))


class RiskDataStore:
    def __init__(self):
        self.postcode_lls_map: dict = {}
        self.lls_valley_map: dict = {}
        self.crop_stats: pd.DataFrame = pd.DataFrame()
        self._load()

    def _load(self):
        self._load_postcode_lls_map()
        self._load_valley_multipliers()
        self._load_crop_stats()

    def _load_postcode_lls_map(self):
        with open(settings.postcode_lls_map_path) as f:
            raw = json.load(f)

        self.postcode_lls_map = {}
        for entry in raw:
            postcode = str(entry.get("postcode", "")).strip()
            suburb = str(entry.get("suburb", "")).strip().upper()
            region_id = entry.get("lls_region_id") or entry.get("lls_region")
            if not postcode or not suburb:
                continue

            fallback_region = _region_slug_from_name(resolve_lls_region(postcode))
            if fallback_region:
                region_id = fallback_region
            elif not region_id:
                continue

            self.postcode_lls_map[(postcode, suburb)] = region_id

    def _load_valley_multipliers(self):
        try:
            df = pd.read_csv(settings.water_allocation_csv_path)
        except FileNotFoundError:
            self.lls_valley_map = {}
            return

        if "lls_region" in df.columns:
            self.lls_valley_map = df.set_index("lls_region").to_dict(orient="index")
            return

        # The repo's water allocation CSV does not use an LLS column; keep a best-effort
        # valley map keyed by the region ID used elsewhere so the loader still works locally.
        self.lls_valley_map = {
            str(value).strip().lower(): {"valley_name": str(value).strip()}
            for value in df.get("water_source", pd.Series(dtype="object")).dropna().unique()
        }

    def _load_crop_stats(self):
        df = pd.read_csv(settings.master_crop_csv_path)
        latest_year = df["year"].max()
        df = df[df["year"] == latest_year]
        self.crop_stats = (
            df.groupby(["region", "crop_category"])["water_intensity_ml_per_ha"]
            .agg(mean="mean", std="std", n="count")
            .reset_index()
            .set_index(["region", "crop_category"])
        )

    def lookup_lls(self, postcode: str, suburb: str) -> dict | None:
        key = (str(postcode), str(suburb or "").strip().upper())
        region_id = self.postcode_lls_map.get(key)
        if region_id is None:
            return None

        valley_info = self.lls_valley_map.get(str(region_id).strip().lower(), {})
        return {
            "region_id": region_id,
            "valley_name": valley_info.get("valley_name") or region_id,
            "allocation_multiplier_min": valley_info.get("allocation_multiplier_min"),
            "allocation_multiplier_max": valley_info.get("allocation_multiplier_max"),
        }

    def lookup_crop_stats(self, region: str, crop_category: str) -> dict | None:
        region_key = str(region or "").strip()
        crop_key = str(crop_category or "").strip()

        candidates = []
        if region_key:
            candidates.append(region_key)
            candidates.append(region_key.title())
            candidates.append(region_key.capitalize())
            candidates.append(region_key.lower())
            candidates.append(region_key.upper())

        if not candidates:
            return None

        for region_candidate in dict.fromkeys(candidates):
            for crop_candidate in dict.fromkeys([crop_key, crop_key.title(), crop_key.lower(), crop_key.upper()]):
                try:
                    row = self.crop_stats.loc[(region_candidate, crop_candidate)]
                    mean = row["mean"]
                    std = row["std"]
                    if pd.isna(mean):
                        mean = None
                    if pd.isna(std):
                        std = None
                    return {"mean": mean, "std": std, "n": int(row["n"])}
                except KeyError:
                    pass

        normalized = self.crop_stats.index.to_series().map(lambda x: (str(x[0]).lower(), str(x[1]).lower()))
        for idx, (region_norm, crop_norm) in normalized.items():
            if region_norm == region_key.lower() and crop_norm == crop_key.lower():
                row = self.crop_stats.loc[idx]
                mean = row["mean"]
                std = row["std"]
                if pd.isna(mean):
                    mean = None
                if pd.isna(std):
                    std = None
                return {"mean": mean, "std": std, "n": int(row["n"])}

        return None


@lru_cache(maxsize=1)
def get_data_store() -> RiskDataStore:
    return RiskDataStore()