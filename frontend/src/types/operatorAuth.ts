export interface OperatorAuthStatus {
  ok: boolean;
  auth_mode: string;
  key_configured: boolean;
  generated_at: string;
}

export interface OperatorAuthVerifyResponse {
  ok: boolean;
  authenticated: boolean;
  message: string;
  generated_at: string;
}
