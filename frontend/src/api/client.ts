const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  "https://nexusmon.onrender.com"
).replace(/\/+$/, "");

function buildHeaders(): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const operatorKey = import.meta.env.VITE_OPERATOR_KEY;
  if (operatorKey && operatorKey.trim() !== "") {
    headers["x-operator-key"] = operatorKey;
  }
  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}
