export type AGUIEventType =
  | "STATE_DELTA"
  | "TOOL_CALL_START"
  | "TOOL_CALL_END"
  | "TEXT_DELTA"
  | "RUN_FINISHED"
  | "ERROR";

export type AGUIEvent = {
  type: AGUIEventType;
  payload: Record<string, unknown>;
};

/**
 * Parse a raw WebSocket message string into an AGUIEvent.
 * Returns null if the message is not a valid AGUI event.
 */
export function parseAGUIEvent(data: string): AGUIEvent | null {
  try {
    const parsed: unknown = JSON.parse(data);
    if (
      parsed === null ||
      typeof parsed !== "object" ||
      Array.isArray(parsed)
    ) {
      return null;
    }
    const obj = parsed as Record<string, unknown>;
    const type = obj["type"];
    if (typeof type !== "string") {
      return null;
    }
    const validTypes: AGUIEventType[] = [
      "STATE_DELTA",
      "TOOL_CALL_START",
      "TOOL_CALL_END",
      "TEXT_DELTA",
      "RUN_FINISHED",
      "ERROR",
    ];
    if (!validTypes.includes(type as AGUIEventType)) {
      return null;
    }
    const payload =
      obj["payload"] !== null &&
      typeof obj["payload"] === "object" &&
      !Array.isArray(obj["payload"])
        ? (obj["payload"] as Record<string, unknown>)
        : {};
    return { type: type as AGUIEventType, payload };
  } catch {
    return null;
  }
}
