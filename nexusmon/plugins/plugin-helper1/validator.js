const Ajv = require("ajv");
const schema = require("./schema.json");

const ajv = new Ajv({ allErrors: true, allowUnionTypes: true });
const validate = ajv.compile(schema);

function validateHelper1(input) {
  const valid = validate(input);
  return { valid, errors: validate.errors || [] };
}

module.exports = validateHelper1;
