# Architecture

```
┌─────────────────┐      /api/*        ┌──────────────────┐     SQL      ┌─────────────┐
│  React (Vite)   │ ───────────────▶  │  FastAPI          │ ──────────▶ │  Supabase   │
│  Tailwind       │  ◀───── JSON ───── │  app/routers/*    │ ◀────────── │  PostgreSQL │
│  PixiJS canvas  │                    │  app/core/algo    │             │             │
│  :5173          │                    │  :8000            │             │  (cloud)    │
└─────────────────┘                    └──────────────────┘             └─────────────┘
```

- **Dev:** Vite proxies `/api` → `localhost:8000`, so there are no CORS issues
  and the frontend code never hardcodes a host.
- **Data flow example (create task):**
  1. `App.jsx` calls `api.createTask(title)` (`src/lib/api.js`)
  2. `POST /tasks` hits `app/routers/tasks.py`
  3. router calls `compute_priority()` in `app/core/algorithm.py`
  4. row inserted via SQLAlchemy into Supabase
  5. created row returned as JSON, React re-renders

## Ownership boundaries

| Concern | Lives in | Don't touch from |
| --- | --- | --- |
| Visual / UI | `frontend/src/` | backend |
| API contract | `backend/app/routers/`, `backend/app/schemas.py` | frontend (propose changes) |
| Persistence | `backend/app/models.py`, `backend/app/db.py` | frontend |
| Algorithm | `backend/app/core/` | everyone else (call it, don't edit it) |
