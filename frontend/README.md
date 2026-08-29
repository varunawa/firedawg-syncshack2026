# Frontend — React + Vite + Tailwind + PixiJS

## Setup

```bash
cd frontend
npm install
cp .env.example .env      # optional in dev
```

## Run

```bash
npm run dev               # http://localhost:5173
```

Run the backend too (`uvicorn app.main:app --reload --port 8000`) — `/api/*`
is proxied there.

## Files

| Path | What it is |
| --- | --- |
| `src/main.jsx` | React entry point |
| `src/App.jsx` | Root component / page |
| `src/components/` | Reusable components (`PixiStage.jsx` here) |
| `src/lib/api.js` | Every backend call, in one place |
| `src/index.css` | `@import "tailwindcss";` — use Tailwind classes in JSX |
| `vite.config.js` | Dev server, `/api` proxy, Tailwind + React plugins |

## Conventions

- Style with Tailwind utility classes directly in JSX. No separate CSS files.
- All network calls go through `src/lib/api.js`. Components never call `fetch`.
- PixiJS lives inside a component that owns a `<div>` and cleans up on unmount
  (see `PixiStage.jsx`).
