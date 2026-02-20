import { BuildMilestonesCard } from "../components/BuildMilestonesCard";
import { useBuildMilestones } from "../hooks/useBuildMilestones";

export function BuildMilestonesPage() {
  const { status, promoteResult, loading, error, refresh, promote } = useBuildMilestones();

  return (
    <BuildMilestonesCard
      status={status}
      promoteResult={promoteResult}
      loading={loading}
      error={error}
      onRefresh={refresh}
      onPromote={promote}
    />
  );
}
