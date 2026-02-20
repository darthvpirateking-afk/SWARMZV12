import { useCallback, useEffect, useState } from "react";
import { fetchApiFoundationDomains, fetchApiFoundationStatus } from "../api/foundation";
import type { ApiFoundationDomains, ApiFoundationStatus } from "../types/apiFoundation";

interface ApiFoundationState {
  status: ApiFoundationStatus | null;
  domains: ApiFoundationDomains | null;
  loading: boolean;
  error: string | null;
}

const initialState: ApiFoundationState = {
  status: null,
  domains: null,
  loading: false,
  error: null,
};

export function useApiFoundation() {
  const [state, setState] = useState<ApiFoundationState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const [status, domains] = await Promise.all([
        fetchApiFoundationStatus(),
        fetchApiFoundationDomains(),
      ]);
      setState({ status, domains, loading: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load API foundation";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    ...state,
    refresh,
  };
}
