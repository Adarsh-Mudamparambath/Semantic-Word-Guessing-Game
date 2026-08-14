const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const BASE = `${API_BASE}/api/game`;

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || "Request failed");
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export function getToday() {
  return request("/today");
}

export function revealSecretWord(gameId) {
  return request(`/reveal?game_id=${encodeURIComponent(gameId)}`);
}

export function startNextRound(gameId) {
  return request("/new-round", {
    method: "POST",
    body: JSON.stringify({ game_id: gameId }),
  });
}

export function submitGuess(gameId, guess) {
  return request("/guess", {
    method: "POST",
    body: JSON.stringify({ game_id: gameId, guess }),
  });
}

export function getHistory(gameId) {
  return request(`/history?game_id=${encodeURIComponent(gameId)}`);
}
