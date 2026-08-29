import { useEffect, useState } from "react";
import { api } from "./lib/api";
import PixiStage from "./components/PixiStage";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState(null);

  async function refresh() {
    try {
      setTasks(await api.listTasks());
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function addTask(e) {
    e.preventDefault();
    if (!title.trim()) return;
    await api.createTask(title.trim());
    setTitle("");
    refresh();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">syncshack-2026</h1>
        <p className="text-sm text-slate-500">
          React + Tailwind + PixiJS · FastAPI · Supabase
        </p>
      </header>

      <PixiStage />

      <form onSubmit={addTask} className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New task title"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-sky-500"
        />
        <button className="rounded-lg bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-700">
          Add
        </button>
      </form>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <ul className="divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200">
        {tasks.length === 0 && (
          <li className="px-4 py-3 text-sm text-slate-400">No tasks yet.</li>
        )}
        {tasks.map((t) => (
          <li key={t.id} className="flex items-center justify-between px-4 py-2">
            <span>{t.title}</span>
            <span className="flex items-center gap-3">
              <span className="font-mono text-xs text-slate-400">
                p{t.priority}
              </span>
              <button
                onClick={async () => {
                  await api.deleteTask(t.id);
                  refresh();
                }}
                className="text-xs text-slate-400 hover:text-red-600"
              >
                delete
              </button>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
