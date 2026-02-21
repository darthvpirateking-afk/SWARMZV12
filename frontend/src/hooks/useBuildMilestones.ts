import { useCallback, useEffect, useState } from "react";
import {
  fetchBuildMilestonesStatus,
  promoteBuildMilestone,
} from "../api/buildMilestones";
import type {
  BuildMilestonesPromoteResponse,
  BuildMilestonesStatus,
} from "../types/buildMilestones";

interface BuildMilestonesState {
  status: BuildMilestonesStatus | null;
  promoteResult: BuildMilestonesPromoteResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: BuildMilestonesState = {
  status: null,
  promoteResult: null,
  loading: false,
  error: null,
};

export function useBuildMilestones() {
  const [state, setState] = useState<BuildMilestonesState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const status = await fetchBuildMilestonesStatus();
      setState((prev) => ({ ...prev, status, loading: false, error: null }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load build milestones";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  const promote = useCallback(async (targetStage: number) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await promoteBuildMilestone(targetStage);
      const status = await fetchBuildMilestonesStatus();
      setState((prev) => ({
        ...prev,
        status,
        promoteResult: result,
        loading: false,
        error: null,
      }));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to promote build";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    ...state,
    refresh,
    promote,
  };
}
