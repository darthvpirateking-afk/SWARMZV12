import { type ReactNode } from "react";
import { useWebSocket } from "../hooks/useWebSocket";

interface Props {
  children: ReactNode;
}

function WebSocketConnector({ children }: Props) {
  useWebSocket();
  return <>{children}</>;
}

export function WebSocketProvider({ children }: Props) {
  return <WebSocketConnector>{children}</WebSocketConnector>;
}
