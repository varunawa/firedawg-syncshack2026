# Backend — FastAPI

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # paste the Supabase DATABASE_URL
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Files

| Path | What it is | Who edits it |
| --- | --- | --- |
| `app/main.py` | App wiring: CORS, routers, startup | backend |
| `app/config.py` | Reads env vars | backend |
| `app/db.py` | SQLAlchemy engine + `get_db()` session | backend |
| `app/models.py` | Database tables | backend |
| `app/schemas.py` | JSON request/response shapes | backend |
| `app/routers/*.py` | Endpoints — one file per resource | backend |
| `app/core/algorithm.py` | Core logic, no web/DB code | algorithm |

## Adding an endpoint

1. Add/extend a model in `app/models.py` if you need to store something.
2. Add schemas in `app/schemas.py`.
3. Create `app/routers/<name>.py` with an `APIRouter` (copy `tasks.py`).
4. `app.include_router(<name>.router)` in `app/main.py`.
5. Add a matching function in `frontend/src/lib/api.js`.
