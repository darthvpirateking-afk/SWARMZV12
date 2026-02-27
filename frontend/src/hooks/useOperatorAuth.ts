import { useCallback, useEffect, useState } from "react";
import {
  fetchOperatorAuthStatus,
  verifyOperatorKey,
} from "../api/operatorAuth";
import type {
  OperatorAuthStatus,
  OperatorAuthVerifyResponse,
} from "../types/operatorAuth";

interface OperatorAuthState {
  status: OperatorAuthStatus | null;
  verifyResult: OperatorAuthVerifyResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: OperatorAuthState = {
  status: null,
  verifyResult: null,
  loading: false,
  error: null,
};

export function useOperatorAuth() {
  const [state, setState] = useState<OperatorAuthState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const status = await fetchOperatorAuthStatus();
      setState((prev) => ({ ...prev, status, loading: false, error: null }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load operator auth status";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  const runVerify = useCallback(async (operatorKey: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await verifyOperatorKey(operatorKey);
      setState((prev) => ({
        ...prev,
        verifyResult: result,
        loading: false,
        error: null,
      }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Operator key verification failed";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    ...state,
    refresh,
    verify: runVerify,
  };
}
