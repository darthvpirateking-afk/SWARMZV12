const { normalizeId, toJson, nowIso } = require("./_shared.js");

async function mission(payload) {
  const missionId = normalizeId(payload.mission_id, "mission-new");
  const title = payload.title || missionId;
  const summary = payload.summary || "Generated mission.";
  const steps = payload.steps.map((step, idx) => ({
    id: normalizeId(step.id || `step-${idx + 1}`, `step-${idx + 1}`),
    action: step.action,
    acceptance: step.acceptance || "Step executes deterministically.",
  }));

  const plan = {
    mission_id: missionId,
    title,
    summary,
    created_at: nowIso(),
    steps,
  };

  return {
    status: "ok",
    task: "mission",
    generated_at: plan.created_at,
    artifacts: [{ path: `config/missions/${missionId}.json`, content: toJson(plan) }],
    summary: { mission_id: missionId, step_count: steps.length },
  };
}

module.exports = mission;
