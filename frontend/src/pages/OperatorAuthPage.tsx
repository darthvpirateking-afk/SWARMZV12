import { OperatorAuthCard } from "../components/OperatorAuthCard";
import { useOperatorAuth } from "../hooks/useOperatorAuth";

export function OperatorAuthPage() {
  const { status, verifyResult, loading, error, refresh, verify } = useOperatorAuth();

  return (
    <OperatorAuthCard
      status={status}
      verifyResult={verifyResult}
      loading={loading}
      error={error}
      onRefresh={refresh}
      onVerify={verify}
    />
  );
}
