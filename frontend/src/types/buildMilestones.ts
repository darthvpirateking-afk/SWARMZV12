export interface BuildStageRecord {
  stage: number;
  title: string;
  status: string;
}

export interface BuildStageExecutionRecord {
  stage: number;
  title: string;
  status: string;
  executed_at: string;
}

export interface BuildMilestonesStatus {
  ok: boolean;
  current_stage: number;
  target_stage: number;
  total_stages: number;
  stages: BuildStageRecord[];
  history: BuildStageExecutionRecord[];
  generated_at: string;
}

export interface BuildMilestonesPromoteResponse {
  ok: boolean;
  current_stage: number;
  target_stage: number;
  applied_stages: BuildStageExecutionRecord[];
  message: string;
  generated_at: string;
}
