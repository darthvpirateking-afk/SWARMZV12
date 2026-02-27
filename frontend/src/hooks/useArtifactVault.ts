import { useCallback, useEffect, useState } from "react";
import {
  artifactsApi,
  type Artifact,
  type ArtifactStats,
  type ArtifactStatus,
} from "../api/artifacts";

interface ArtifactVaultState {
  artifacts: Artifact[];
  stats: ArtifactStats | null;
  total: number;
  loading: boolean;
  error: string | null;
  actionError: string | null;
}

const initialState: ArtifactVaultState = {
  artifacts: [],
  stats: null,
  total: 0,
  loading: false,
  error: null,
  actionError: null,
};

export function useArtifactVault(statusFilter?: ArtifactStatus) {
  const [state, setState] = useState<ArtifactVaultState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const [listRes, statsRes] = await Promise.allSettled([
        artifactsApi.list({ status: statusFilter, limit: 50 }),
        artifactsApi.stats(),
      ]);

      const artifacts =
        listRes.status === "fulfilled" ? listRes.value.artifacts : [];
      const total =
        listRes.status === "fulfilled" ? listRes.value.total : 0;
      const stats =
        statsRes.status === "fulfilled" ? statsRes.value : null;

      setState((prev) => ({
        ...prev,
        artifacts,
        stats,
        total,
        loading: false,
        error: null,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load artifacts",
      }));
    }
  }, [statusFilter]);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 15_000);
    return () => clearInterval(id);
  }, [refresh]);

  const approve = useCallback(
    async (id: string) => {
      setState((prev) => ({ ...prev, actionError: null }));
      try {
        await artifactsApi.approve(id);
        await refresh();
      } catch (err) {
        setState((prev) => ({
          ...prev,
          actionError:
            err instanceof Error ? err.message : "Approve failed",
        }));
      }
    },
    [refresh],
  );

  const reject = useCallback(
    async (id: string) => {
      setState((prev) => ({ ...prev, actionError: null }));
      try {
        await artifactsApi.reject(id);
        await refresh();
      } catch (err) {
        setState((prev) => ({
          ...prev,
          actionError:
            err instanceof Error ? err.message : "Reject failed",
        }));
      }
    },
    [refresh],
  );

  return { ...state, refresh, approve, reject };
}
