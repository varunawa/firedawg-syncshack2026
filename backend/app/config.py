from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

def _find_repo_root(marker: str = ".git") -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / marker).exists():
            return parent
    raise RuntimeError(f"Could not locate repo root above {current}")

_REPO_ROOT = _find_repo_root()
_BACKEND_ROOT = _REPO_ROOT / "backend"
_DATA_DIR = _REPO_ROOT / "data"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./local.db"
    CORS_ORIGINS: str = "http://localhost:5173"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        placeholders = ("YOUR_PROJECT_REF", "YOUR_PASSWORD", "YOUR_")
        if not value or any(token in value for token in placeholders):
            return "sqlite:///./local.db"
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    postcode_lls_map_path: Path = _BACKEND_ROOT / "postcode_lls_map.json"
    australian_postcodes_csv_path: Path = _BACKEND_ROOT / "australian_postcodes.csv"
    master_crop_csv_path: Path = _DATA_DIR / "MASTER_CROP.csv"
    water_allocation_csv_path: Path = _DATA_DIR / "water_allocation.csv"
    strategy_catalog_path: Path = _DATA_DIR / "strategy_catalog.json"


settings = Settings()  # type: ignore[call-arg]
