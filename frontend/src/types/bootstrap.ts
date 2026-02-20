export interface BootstrapChecks {
  data_dir_exists: boolean;
  audit_log_exists: boolean;
  missions_log_exists: boolean;
}

export interface BootstrapStatus {
  ok: boolean;
  service: string;
  version: string;
  environment: string;
  generated_at: string;
  checks: BootstrapChecks;
  warnings: string[];
}
