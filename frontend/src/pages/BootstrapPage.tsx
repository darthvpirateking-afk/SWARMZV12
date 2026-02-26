import { BootstrapStatusCard } from "../components/BootstrapStatusCard";
import { useBootstrapStatus } from "../hooks/useBootstrapStatus";

export function BootstrapPage() {
  const { status, loading, error, refresh } = useBootstrapStatus();

  return (
    <BootstrapStatusCard
      status={status}
      loading={loading}
      error={error}
      onRefresh={refresh}
    />
  );
}
