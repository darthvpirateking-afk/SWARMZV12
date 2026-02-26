import { apiGet, apiPost } from "./client";

export type ArtifactStatus = "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "ARCHIVED";
export type ArtifactType =
  | "TEXT"
  | "CODE"
  | "DATA"
  | "REPORT"
  | "ANALYSIS"
  | "DECISION"
  | "LOG";

export interface Artifact {
  id: string;
  version: number;
  mission_id: string | null;
  task_id: string;
  type: ArtifactType;
  title: string;
  content: unknown;
  input_snapshot: Record<string, unknown>;
  status: ArtifactStatus;
  operator_notes: string;
  created_at: string;
  reviewed_at: string;
  reviewed_by: string;
  previous_version_id: string;
}

export interface ArtifactStats {
  total: number;
  pending_review: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

interface _ListResponse {
  ok: boolean;
  artifacts: Artifact[];
  count: number;
}

interface _SingleResponse {
  ok: boolean;
  artifact: Artifact;
}

interface _StatsResponse {
  ok: boolean;
  total: number;
  pending_review: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

interface _HistoryResponse {
  ok: boolean;
  history: Artifact[];
  versions: number;
}

export const artifactsApi = {
  stats: () =>
    apiGet<_StatsResponse>("/v1/vault/artifacts/stats").then(
      (r): ArtifactStats => ({
        total: r.total,
        pending_review: r.pending_review,
        by_status: r.by_status,
        by_type: r.by_type,
      }),
    ),

  list: (params?: {
    status?: ArtifactStatus;
    type?: ArtifactType;
    mission_id?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.type) qs.set("type", params.type);
    if (params?.mission_id) qs.set("mission_id", params.mission_id);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return apiGet<_ListResponse>(
      `/v1/vault/artifacts${q ? "?" + q : ""}`,
    ).then((r) => ({ artifacts: r.artifacts, total: r.count }));
  },

  get: (id: string) =>
    apiGet<_SingleResponse>(`/v1/vault/artifacts/${id}`).then(
      (r) => r.artifact,
    ),

  create: (body: {
    mission_id: string;
    task_id?: string;
    type: ArtifactType;
    title: string;
    content?: unknown;
  }) =>
    apiPost<_SingleResponse>("/v1/vault/artifacts", body).then(
      (r) => r.artifact,
    ),

  approve: (id: string) =>
    apiPost<_SingleResponse>(`/v1/vault/artifacts/${id}/approve`, {}).then(
      (r) => r.artifact,
    ),

  reject: (id: string) =>
    apiPost<_SingleResponse>(`/v1/vault/artifacts/${id}/reject`, {}).then(
      (r) => r.artifact,
    ),

  history: (id: string) =>
    apiGet<_HistoryResponse>(`/v1/vault/artifacts/${id}/history`).then(
      (r) => r.history,
    ),

  byMission: (missionId: string) =>
    apiGet<_ListResponse>(`/v1/vault/missions/${missionId}/artifacts`).then(
      (r) => ({ artifacts: r.artifacts, total: r.count }),
    ),
};

