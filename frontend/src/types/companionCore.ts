export interface CompanionCoreStatus {
  ok: boolean;
  source: string;
  memory_version: number;
  outcomes_count: number;
  summary: string;
  generated_at: string;
}

export interface CompanionCoreMessageResponse {
  ok: boolean;
  reply: string;
  source: string;
  generated_at: string;
}
