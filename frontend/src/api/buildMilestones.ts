import { apiGet, apiPost } from "./client";
import type {
  BuildMilestonesPromoteResponse,
  BuildMilestonesStatus,
} from "../types/buildMilestones";

export function fetchBuildMilestonesStatus(): Promise<BuildMilestonesStatus> {
  return apiGet<BuildMilestonesStatus>("/v1/build/milestones/status");
}

export function promoteBuildMilestone(
  target_stage: number,
): Promise<BuildMilestonesPromoteResponse> {
  return apiPost<BuildMilestonesPromoteResponse>(
    "/v1/build/milestones/promote",
    { target_stage },
  );
}
