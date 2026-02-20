import { ApiFoundationCard } from "../components/ApiFoundationCard";
import { useApiFoundation } from "../hooks/useApiFoundation";

export function ApiFoundationPage() {
  const { status, domains, loading, error, refresh } = useApiFoundation();
  return (
    <ApiFoundationCard
      status={status}
      domains={domains}
      loading={loading}
      error={error}
      onRefresh={refresh}
    />
  );
}
