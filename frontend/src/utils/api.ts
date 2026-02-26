/**
 * Generic API POST helper
 */
export async function apiPost<T>(
  endpoint: string,
  payload: Record<string, unknown>
): Promise<T> {
  const url = new URL(endpoint, window.location.origin);

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
