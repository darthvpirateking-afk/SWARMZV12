export async function getHealth() {
  const res = await fetch("/health");
  return res.json();
}

export async function getGovernor() {
  try {
    const res = await fetch("/api/governor");
    return res.json();
  } catch {
    return { ok: false, error: "governor unavailable" };
  }
}
