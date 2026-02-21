import { apiGet, apiPost } from "./client";
import type {
  OperatorAuthStatus,
  OperatorAuthVerifyResponse,
} from "../types/operatorAuth";

export function fetchOperatorAuthStatus(): Promise<OperatorAuthStatus> {
  return apiGet<OperatorAuthStatus>("/v1/operator/auth/status");
}

export function verifyOperatorKey(
  operator_key: string,
): Promise<OperatorAuthVerifyResponse> {
  return apiPost<OperatorAuthVerifyResponse>("/v1/operator/auth/verify", {
    operator_key,
  });
}
