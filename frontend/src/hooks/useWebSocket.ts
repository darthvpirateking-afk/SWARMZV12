import { useEffect, useRef, useCallback } from "react";
import { useSystemStore } from "../stores/systemStore";
import { useMissionStore } from "../stores/missionStore";
import { useCockpitStore } from "../stores/cockpitStore";

interface WSMessage {
  channel: string;
  data: Record<string, unknown>;
  timestamp: string;
}

const WS_URL =
  (import.meta as unknown as { env: Record<string, string> }).env
    ?.VITE_WS_URL || `ws://${window.location.host}/ws/cockpit`;

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const updateSystem = useSystemStore((s) => s.updateFromHealth);
  const setMissions = useMissionStore((s) => s.setMissions);
  const addMission = useMissionStore((s) => s.addMission);
  const updateMission = useMissionStore((s) => s.updateMission);
  const updateCockpit = useCockpitStore((s) => s.updateFromCommandCenter);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttempt.current = 0;
        // Subscribe to all channels
        ws.send(
          JSON.stringify({
            subscribe: ["system", "missions", "evolution", "command-center"],
          }),
        );
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          dispatch(msg);
        } catch {
          // Non-JSON messages (welcome, pong, etc.)
        }
      };

      ws.onclose = () => {
        scheduleReconnect();
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      scheduleReconnect();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleReconnect = useCallback(() => {
    const delay =
      RECONNECT_DELAYS[
        Math.min(reconnectAttempt.current, RECONNECT_DELAYS.length - 1)
      ];
    reconnectAttempt.current += 1;
    reconnectTimer.current = setTimeout(connect, delay);
  }, [connect]);

  const dispatch = useCallback(
    (msg: WSMessage) => {
      const { channel, data } = msg;

      switch (channel) {
        case "system":
          updateSystem(data as Parameters<typeof updateSystem>[0]);
          break;
        case "missions":
          if (data.type === "list") {
            setMissions(
              data.missions as Parameters<typeof setMissions>[0],
            );
          } else if (data.type === "created") {
            addMission(
              data.mission as Parameters<typeof addMission>[0],
            );
          } else if (data.type === "updated" && data.mission_id) {
            updateMission(
              data.mission_id as string,
              data.updates as Record<string, unknown>,
            );
          }
          break;
        case "command-center":
        case "evolution":
          updateCockpit(data);
          break;
      }
    },
    [updateSystem, setMissions, addMission, updateMission, updateCockpit],
  );

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { send, disconnect, reconnect: connect };
}
