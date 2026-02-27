import { useCallback, useEffect, useState } from "react";
import {
  fetchDatabaseCollections,
  fetchDatabaseStats,
  fetchDatabaseStatus,
} from "../api/database";
import type {
  DatabaseCollections,
  DatabaseStats,
  DatabaseStatus,
} from "../types/databaseLayer";

interface DatabaseLayerState {
  status: DatabaseStatus | null;
  collections: DatabaseCollections | null;
  stats: DatabaseStats | null;
  loading: boolean;
  error: string | null;
}

const initialState: DatabaseLayerState = {
  status: null,
  collections: null,
  stats: null,
  loading: false,
  error: null,
};

export function useDatabaseLayer() {
  const [state, setState] = useState<DatabaseLayerState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const [status, collections, stats] = await Promise.all([
        fetchDatabaseStatus(),
        fetchDatabaseCollections(),
        fetchDatabaseStats(),
      ]);
      setState({ status, collections, stats, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load database layer";
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
