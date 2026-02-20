import { useCallback, useEffect, useState } from "react";
import {
  fetchCompanionCoreStatus,
  sendCompanionCoreMessage,
} from "../api/companionCore";
import type {
  CompanionCoreMessageResponse,
  CompanionCoreStatus,
} from "../types/companionCore";

interface CompanionCoreState {
  status: CompanionCoreStatus | null;
  messageResult: CompanionCoreMessageResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: CompanionCoreState = {
  status: null,
  messageResult: null,
  loading: false,
  error: null,
};

export function useCompanionCore() {
  const [state, setState] = useState<CompanionCoreState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const status = await fetchCompanionCoreStatus();
      setState((prev) => ({ ...prev, status, loading: false, error: null }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load companion core status";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  const message = useCallback(async (text: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await sendCompanionCoreMessage(text);
      setState((prev) => ({ ...prev, messageResult: result, loading: false, error: null }));
    } catch (error) {
      const payload = error instanceof Error ? error.message : "Failed to send companion core message";
      setState((prev) => ({ ...prev, loading: false, error: payload }));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    ...state,
    refresh,
    message,
  };
}
