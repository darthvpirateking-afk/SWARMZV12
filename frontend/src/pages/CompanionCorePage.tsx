import { CompanionCoreCard } from "../components/CompanionCoreCard";
import { useCompanionCore } from "../hooks/useCompanionCore";

export function CompanionCorePage() {
  const { status, messageResult, loading, error, refresh, message } =
    useCompanionCore();

  return (
    <CompanionCoreCard
      status={status}
      messageResult={messageResult}
      loading={loading}
      error={error}
      onRefresh={refresh}
      onMessage={message}
    />
  );
}
