import { apiGet } from "./client";
import type { BootstrapStatus } from "../types/bootstrap";

export function fetchBootstrapStatus(): Promise<BootstrapStatus> {
  return apiGet<BootstrapStatus>("/v1/bootstrap/status");
}
