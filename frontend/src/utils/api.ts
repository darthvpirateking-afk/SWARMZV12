/**
 * Generic API POST helper
 */
export async function apiPost<T>(
  endpoint: string,
  payload: Record<string, unknown>
): Promise<T> {
  // Canonical API env with backward-compatible fallback.
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    window.location.origin;
  const url = new URL(endpoint, baseUrl);

  const response = await fetch(url.toString(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `HTTP ${response.status}: ${errorText || response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}
