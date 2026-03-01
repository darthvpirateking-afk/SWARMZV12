export type AGUIEvent = {
  type: string;
  payload: Record<string, unknown>;
};

export function parseAGUIEvent(data: string): AGUIEvent | null {
  try {
    const event = JSON.parse(data);
    if (
      event &&
      typeof event.type === "string" &&
      typeof event.payload === "object" &&
      event.payload !== null &&
      !Array.isArray(event.payload)
    ) {
    if (event && typeof event.type === "string" && typeof event.payload === "object") {
      return event as AGUIEvent;
    }
    return null;
  } catch {
    return null;
  }
}
}
