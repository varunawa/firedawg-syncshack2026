// The ONE place the frontend talks to the backend.
// Keep every endpoint call here so the API surface is easy to see and change.

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText} — ${body}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  health: () => request("/health"),
  listTasks: () => request("/tasks"),
  createTask: (title) =>
    request("/tasks", { method: "POST", body: JSON.stringify({ title }) }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: "DELETE" }),
};
