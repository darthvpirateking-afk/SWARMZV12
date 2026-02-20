import type { BootstrapStatus } from "../types/bootstrap";

export interface BootstrapStoreState {
  status: BootstrapStatus | null;
  loading: boolean;
  error: string | null;
}

export const bootstrapInitialState: BootstrapStoreState = {
  status: null,
  loading: false,
  error: null,
};
