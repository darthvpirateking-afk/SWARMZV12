import { useEffect, useMemo, useRef, useState } from "react";
import { parseAGUIEvent, type AGUIEvent } from "../lib/agui_protocol";

type AGUIHandlers = {
  onStateDelta?: (payload: Record<string, unknown>) => void;
  onToolCallStart?: (payload: Record<string, unknown>) => void;
  onToolCallEnd?: (payload: Record<string, unknown>) => void;
  onTextDelta?: (payload: Record<string, unknown>) => void;
  onRunFinished?: (payload: Record<string, unknown>) => void;
  onError?: (payload: Record<string, unknown>) => void;
};

export function useAGUI(url: string, handlers: AGUIHandlers = {}) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<AGUIEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      const msg = parseAGUIEvent(String(event.data));
      if (!msg) {
        return;
      }

      setLastEvent(msg);
      switch (msg.type) {
        case "STATE_DELTA":
          handlers.onStateDelta?.(msg.payload);
          break;
        case "TOOL_CALL_START":
          handlers.onToolCallStart?.(msg.payload);
          break;
        case "TOOL_CALL_END":
          handlers.onToolCallEnd?.(msg.payload);
          break;
        case "TEXT_DELTA":
          handlers.onTextDelta?.(msg.payload);
          break;
        case "RUN_FINISHED":
          handlers.onRunFinished?.(msg.payload);
          break;
        case "ERROR":
          handlers.onError?.(msg.payload);
          break;
        default:
          break;
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [url]);

  const send = useMemo(
    () => (payload: Record<string, unknown>) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(payload));
      }
    },
    [],
  );

  return {
    connected,
    lastEvent,
    send,
  };
}
