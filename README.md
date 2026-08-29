# syncshack-2026

Hackathon project.

| Layer | Stack | Folder |
| --- | --- | --- |
| Frontend | React + Vite + Tailwind CSS + PixiJS | [`frontend/`](frontend/) |
| Backend | FastAPI + SQLAlchemy (+ your algorithm) | [`backend/`](backend/) |
| Database | Supabase (hosted PostgreSQL) | — |

```
syncshack-2026/
├── frontend/     React app          → frontend/README.md
├── backend/      FastAPI API + algo → backend/README.md
└── docs/         notes & diagrams
```

---

## Quick start (after cloning)

You need **Node 20+**, **Python 3.11+**, and the Supabase connection string
(ask whoever set up the Supabase project — it is shared privately, never in git).

### 1. Backend — terminal 1

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # paste the Supabase DATABASE_URL into .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs — interactive API docs.

### 2. Frontend — terminal 2

```bash
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

The frontend proxies `/api/*` to the backend on port 8000, so run both.

---

## Who works on what

| Person | Owns | Works in |
| --- | --- | --- |
| Frontend | UI, PixiJS canvas, calling the API | `frontend/src/` |
| Backend | API endpoints, DB models, request/response shapes | `backend/app/routers/`, `backend/app/models.py` |
| Algorithm | Core logic, kept pure & testable | `backend/app/core/algorithm.py` |

The frontend↔backend contract is the set of endpoints in `backend/app/routers/`
and the matching functions in `frontend/src/lib/api.js`. Agree on changes there.

---

## Git workflow

`main` stays runnable at all times. Nobody pushes to `main` directly.

```bash
git checkout main && git pull            # start from latest
git checkout -b feat/short-description    # your branch
# ... work, commit ...
git push -u origin feat/short-description
```

Then open a Pull Request on GitHub, get one teammate to review, and merge.
Suggested branch prefixes: `feat/`, `fix/`, `chore/`.

**Never commit `.env`** — only `.env.example` is tracked.
