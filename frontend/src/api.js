const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";
const WS_BASE_URL = BASE_URL.replace(/^http/, "ws");

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("token", token);
  } else {
    localStorage.removeItem("token");
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // no JSON body
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) return null;
  return response.json();
}

export function register({
  username,
  email,
  password,
  cr_player_tag,
  phone_number,
  supercell_id_link,
}) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      email,
      password,
      cr_player_tag,
      phone_number,
      supercell_id_link,
    }),
  });
}

export async function login({ email, password }) {
  const body = new URLSearchParams({ username: email, password });
  const data = await request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  setToken(data.access_token);
  return data;
}

export function getMe() {
  return request("/auth/me");
}

export function getBalance() {
  return request("/wallet/balance");
}

export function deposit(amount) {
  return request("/wallet/deposit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  });
}

export function withdraw(amount) {
  return request("/wallet/withdraw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  });
}

export function getTransactions() {
  return request("/wallet/transactions");
}

export function queueMatch(stakeAmount) {
  return request("/matchmaking/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stake_amount: stakeAmount }),
  });
}

export function cancelQueue() {
  return request("/matchmaking/queue", { method: "DELETE" });
}

export function getMatchmakingStatus() {
  return request("/matchmaking/status");
}

export function getWagers() {
  return request("/wagers");
}

export function matchmakingSocketUrl() {
  const token = getToken();
  return `${WS_BASE_URL}/matchmaking/ws?token=${encodeURIComponent(token)}`;
}
