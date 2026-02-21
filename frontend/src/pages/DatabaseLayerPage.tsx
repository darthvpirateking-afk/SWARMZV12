import { DatabaseLayerCard } from "../components/DatabaseLayerCard";
import { useDatabaseLayer } from "../hooks/useDatabaseLayer";

export function DatabaseLayerPage() {
  const { status, collections, stats, loading, error, refresh } =
    useDatabaseLayer();
  return (
    <DatabaseLayerCard
      status={status}
      collections={collections}
      stats={stats}
      loading={loading}
      error={error}
      onRefresh={refresh}
    />
  );
}
