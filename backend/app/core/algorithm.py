"""The core algorithm lives here, deliberately isolated from FastAPI and the DB.

Rules of thumb:
- pure functions: inputs -> outputs, no database calls, no globals
- the router calls into this module, not the other way around
- add tests in backend/tests/ so this can evolve without breaking the API
"""


def compute_priority(title: str) -> int:
    """Placeholder. Replace with the real scoring/ranking/matching logic."""
    weight = len(title.split())
    return min(100, weight * 10)
