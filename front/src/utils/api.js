const BASE = process.env.REACT_APP_API_URL || "";

async function request(path, options = {}) {
  const token = localStorage.getItem("masters_token");
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),

  auth: {
    register: (u, e, p) => request("/api/auth/register", {
      method: "POST", body: JSON.stringify({ username: u, email: e, password: p })
    }),
    login: (u, p) => request("/api/auth/login", {
      method: "POST", body: JSON.stringify({ username: u, password: p })
    }),
    me: () => request("/api/auth/me"),
  },
  golfers: {
    list: () => request("/api/golfers"),
  },
  teams: {
    submit: (team_name, golfer_ids) =>
      request("/api/teams/submit", { method: "POST", body: JSON.stringify({ team_name, golfer_ids }) }),
    my: () => request("/api/teams/my"),
    get: (id) => request(`/api/teams/${id}`),
  },
  leaderboard: {
    get: () => request("/api/leaderboard"),
  },
  admin: {
    lockTeams:    () => request("/api/admin/lock-teams", { method: "POST" }),
    unlockTeams:  () => request("/api/admin/unlock-teams", { method: "POST" }),
    refresh:      () => request("/api/admin/refresh-scores", { method: "POST" }),
    users:        () => request("/api/admin/users"),
    updateGolfer: (body) =>
      request("/api/admin/update-golfer", { method: "POST", body: JSON.stringify(body) }),
    setRound:     (n) => request(`/api/admin/set-round?round_num=${n}`, { method: "POST" }),
    deleteTeams: (team_ids) => request("/api/admin/delete-teams", { method: "POST", body: JSON.stringify({ team_ids }) }),
    clearTeams: () => request("/api/admin/clear-teams", { method: "POST" }),
    clearScores: () => request("/api/admin/clear-scores", { method: "POST" }),
  },
};

export { api };