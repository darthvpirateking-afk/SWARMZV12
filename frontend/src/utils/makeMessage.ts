import { v4 as uuidv4 } from "uuid";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

/**
 * Create a new chat message with unique ID
 */
export function makeMessage(
  role: "user" | "assistant",
  text: string
): ChatMessage {
  return {
    id: uuidv4(),
    role,
    text,
  };
}
