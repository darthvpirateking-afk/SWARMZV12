function resolveBaseUrl(): string {
  const env = (import.meta as any)?.env ?? {};
  const base = env.VITE_API_BASE_URL || env.VITE_API_URL || "http://localhost:8000";
  return String(base).replace(/\/+$/, "");
}

const API_BASE_URL = resolveBaseUrl();

export async function getHealth() {
  const res = await fetch(`${API_BASE_URL}/health/ready`);
  return res.json();
}

export async function getGovernor() {
  const res = await fetch(`${API_BASE_URL}/api/governor`);
  return res.json();
}

export async function runHelper1(query: string) {
  const res = await fetch(`${API_BASE_URL}/v1/agents/helper1/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Operator-Approval": "approved",
    },
    body: JSON.stringify({ query }),
  });
  return res.json();
}

export async function getCanonicalAgents() {
  const res = await fetch(`${API_BASE_URL}/v1/canonical/agents`);
  return res.json();
}

export async function getRecentTraces(limit = 25) {
  const res = await fetch(`${API_BASE_URL}/v1/canonical/traces/recent?limit=${limit}`);
  return res.json();
}
