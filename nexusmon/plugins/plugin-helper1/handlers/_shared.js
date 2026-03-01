function normalizeId(value, fallback) {
  const raw = typeof value === "string" ? value : fallback;
  return raw.toLowerCase().replace(/[^a-z0-9-_]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

function toJson(value) {
  return JSON.stringify(value, null, 2) + "\n";
}

function nowIso() {
  return new Date().toISOString();
}

module.exports = {
  normalizeId,
  toJson,
  nowIso,
};
