import { apiGet, apiPost } from "./client";
import type {
  CompanionCoreMessageResponse,
  CompanionCoreStatus,
} from "../types/companionCore";

export function fetchCompanionCoreStatus(): Promise<CompanionCoreStatus> {
  return apiGet<CompanionCoreStatus>("/v1/companion/core/status");
}

export function sendCompanionCoreMessage(text: string): Promise<CompanionCoreMessageResponse> {
  return apiPost<CompanionCoreMessageResponse>("/v1/companion/core/message", { text });
}
