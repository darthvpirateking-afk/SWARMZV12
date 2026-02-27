import { useCallback, useEffect, useState } from "react";
import { fetchBootstrapStatus } from "../api/bootstrap";
import {
  bootstrapInitialState,
  type BootstrapStoreState,
} from "../stores/bootstrapStore";

export function useBootstrapStatus() {
  const [state, setState] = useState<BootstrapStoreState>(
    bootstrapInitialState,
  );

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const status = await fetchBootstrapStatus();
      setState({ status, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Bootstrap status request failed";
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
