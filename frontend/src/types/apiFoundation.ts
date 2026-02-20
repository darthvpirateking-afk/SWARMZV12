export interface ApiFoundationStatus {
  ok: boolean;
  service: string;
  api_version: string;
  generated_at: string;
  route_count: number;
  domains: string[];
  capabilities: string[];
}

export interface ApiFoundationDomains {
  ok: boolean;
  generated_at: string;
  domains: string[];
}
