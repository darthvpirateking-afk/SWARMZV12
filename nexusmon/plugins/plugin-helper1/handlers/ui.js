const { normalizeId, toJson, nowIso } = require("./_shared.js");

async function ui(payload) {
  const viewId = normalizeId(payload.view_id, "generated-view");
  const panel = {
    id: viewId,
    title: payload.title || viewId,
    layout: payload.layout || "stack",
    sections: payload.sections,
    generated_at: nowIso(),
  };

  return {
    status: "ok",
    task: "ui",
    generated_at: panel.generated_at,
    artifacts: [{ path: `ui/panels/${viewId}.json`, content: toJson(panel) }],
    summary: { view_id: viewId, section_count: payload.sections.length },
  };
}

module.exports = ui;
