const validateHelper1 = require("./validator.js");
const generate = require("./handlers/generate.js");
const mission = require("./handlers/mission.js");
const schema = require("./handlers/schema.js");
const ui = require("./handlers/ui.js");
const patchpack = require("./handlers/patchpack.js");

async function HELPER1(input) {
  const { valid, errors } = validateHelper1(input);
  if (!valid) {
    return { status: "error", error: "Invalid input", details: errors };
  }

  const payload = input.payload || {};
  switch (input.task) {
    case "generate":
      return generate(payload);
    case "mission":
      return mission(payload);
    case "schema":
      return schema(payload);
    case "ui":
      return ui(payload);
    case "patchpack":
      return patchpack(payload);
    default:
      return {
        status: "error",
        error: "Unknown task",
        allowed_tasks: ["generate", "mission", "schema", "ui", "patchpack"],
      };
  }
}

module.exports = HELPER1;
