import { apiGet } from "./client";
import type {
  ApiFoundationDomains,
  ApiFoundationStatus,
} from "../types/apiFoundation";

export function fetchApiFoundationStatus(): Promise<ApiFoundationStatus> {
  return apiGet<ApiFoundationStatus>("/v1/api/status");
}

export function fetchApiFoundationDomains(): Promise<ApiFoundationDomains> {
  return apiGet<ApiFoundationDomains>("/v1/api/domains");
}
