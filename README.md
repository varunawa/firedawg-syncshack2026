# H2.OS — water risk assessment for NSW farms

SyncsHack 2026 project.

A NSW farmer enters their location, crop, water use and land size. H2.OS:

1. **Benchmarks** their water intensity (ML applied per hectare) against ABS
   *Water Use on Australian Farms* data for their Local Land Services region and
   crop, and scores it with a z-score against comparable NSW regions.
2. Layers in **local water conditions** — WaterNSW dam allocations and
   Open-Meteo rainfall / evapotranspiration — to produce a **water risk rating**.
3. Recommends **water-saving strategies** with projected ML and dollar savings.
4. Runs an **ML model** predicting expected water intensity for the region/crop.
5. Generates a **plain-English summary** of the result with Google Gemini.

| Layer | Stack | Folder |
| --- | --- | --- |
| Frontend | React + Vite + TypeScript + Tailwind + PixiJS | [`frontend/`](frontend/) |
| Backend | FastAPI + SQLAlchemy + pandas / NumPy / scikit-learn | [`backend/`](backend/) |
| Database | Supabase (hosted PostgreSQL) | — |
| External | Google Gemini, WaterNSW WaterInsights, Open-Meteo | — |

```
syncshack-2026/
├── frontend/     React app                → frontend/README.md
├── backend/      FastAPI API + analytics  → backend/README.md
├── data/         benchmark CSVs, strategy catalog, ML training data
├── ml/           trained model artifact (water_intensity_model.joblib)
└── docs/         notes & diagrams
```

---

## Quick start (after cloning)

You need **Node 20+**, **Python 3.12+**, and the shared secrets (Supabase
connection string, API keys) — ask a teammate; they are shared privately, never
in git.

### 1. Backend — terminal 1

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # then fill in .env — see below
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs — interactive API docs.

Re-run `pip install -r requirements.txt` whenever you pull and something errors
with `ModuleNotFoundError` — it means a dependency was added.

### 2. Frontend — terminal 2

```bash
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

The frontend proxies `/api/*` to the backend on port 8000, so run both.

---

## Environment variables (`backend/.env`)

Copy `backend/.env.example` and fill in. **Never commit `.env`** — it's gitignored.

| Var | Required? | What it's for |
| --- | --- | --- |
| `DATABASE_URL` | recommended | Supabase Postgres connection string. Falls back to local SQLite if unset/placeholder. |
| `CORS_ORIGINS` | no | Comma-separated allowed origins. Default `http://localhost:5173`. |
| `WATERNSW_API_KEY` / `WATERNSW_API_SECRET` | yes to boot | WaterNSW WaterInsights API. The app won't start without these — use dummy values locally if you don't need live dam data: `WATERNSW_API_KEY=dummy WATERNSW_API_SECRET=dummy uvicorn ...` |
| `GEMINI_API_KEY` | optional | Google AI Studio key (free — https://aistudio.google.com/apikey). Without it, `/analyse/explain` returns `explanation: null` and the UI just hides the summary card. Each teammate needs their own, or share one — the free daily quota is per key. |
| `GEMINI_MODEL` | optional | Default `gemini-3.1-flash-lite` (large free-tier quota). |

---

## API endpoints

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/analyse` | Benchmark comparison — water intensity, z-score, rating |
| `POST` | `/analyse/explain` | Plain-English summary of an `/analyse` result (Gemini) |
| `POST` | `/recommend-strategies` | Risk score + optimised water-saving strategy list |
| `POST` | `/prediction` | ML-predicted water intensity for a region/crop |
| `GET` | `/api/weather?location=` | Weather / rainfall for a place (Open-Meteo) |
| `GET` | `/api/water/dams…` | WaterNSW dam storage & allocation data |
| `GET` | `/health` | Liveness check |

The frontend↔backend contract is these endpoints + [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts).
Agree on changes there.

---

## Repo layout — backend

| Path | What it is |
| --- | --- |
| `app/main.py` | App wiring: CORS, routers, startup |
| `app/config.py` | Env config + resolved data-file paths |
| `app/routers/*.py` | HTTP endpoints — thin, one file per concern |
| `app/services/*.py` | External integrations + orchestration (weather, WaterNSW, Gemini, optimizer, risk, ML) |
| `app/core/*.py` | Pure functions — benchmark maths, LLS region lookup. No web/DB code. Unit-tested in `backend/tests/`. |
| `app/schemas.py` | Pydantic request/response shapes |
| `app/models.py` / `app/db.py` | SQLAlchemy tables + session |

---

## Git workflow

`main` stays runnable at all times. Nobody pushes to `main` directly.

```bash
git checkout main && git pull            # start from latest
git checkout -b feat/short-description    # your branch
# ... work, commit ...
git push -u origin feat/short-description
```

Then open a Pull Request, get one teammate to review, and merge. Branch
prefixes: `feat/`, `fix/`, `chore/`.

CI (GitHub Actions) runs the backend test suite (`pytest`) and a frontend
production build on every PR.

**Never commit `.env`** — only `.env.example` is tracked.
