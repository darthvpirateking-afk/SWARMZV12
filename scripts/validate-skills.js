#!/usr/bin/env node
/**
 * Skill Definition Validator
 * Validates all skill JSON files in the skills/ directory.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const REQUIRED_FIELDS = ['name', 'version', 'description', 'category', 'inputs', 'outputs'];

const skillsDir = path.resolve(__dirname, '..', 'skills');

function validateInput(input, skillName, idx) {
  const required = ['name', 'type'];
  let valid = true;
  for (const field of required) {
    if (!input[field]) {
      console.error(`  ERROR: ${skillName} input[${idx}] missing required field: "${field}"`);
      valid = false;
    }
  }
  return valid;
}

function validateOutput(output, skillName, idx) {
  const required = ['name', 'type'];
  let valid = true;
  for (const field of required) {
    if (!output[field]) {
      console.error(`  ERROR: ${skillName} output[${idx}] missing required field: "${field}"`);
      valid = false;
    }
  }
  return valid;
}

function validateSkill(filePath) {
  const rel = path.relative(process.cwd(), filePath);
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    console.error(`  ERROR: Could not parse ${rel}: ${err.message}`);
    return false;
  }

  let valid = true;
  for (const field of REQUIRED_FIELDS) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      console.error(`  ERROR: ${rel} missing required field: "${field}"`);
      valid = false;
    }
  }

  if (!Array.isArray(data.inputs)) {
    console.error(`  ERROR: ${rel} - "inputs" must be an array`);
    valid = false;
  } else {
    data.inputs.forEach((inp, i) => {
      if (!validateInput(inp, rel, i)) valid = false;
    });
  }

  if (!Array.isArray(data.outputs)) {
    console.error(`  ERROR: ${rel} - "outputs" must be an array`);
    valid = false;
  } else {
    data.outputs.forEach((out, i) => {
      if (!validateOutput(out, rel, i)) valid = false;
    });
  }

  if (valid) {
    console.log(`  OK: ${rel} (${data.name}@${data.version})`);
  }
  return valid;
}

function main() {
  if (!fs.existsSync(skillsDir)) {
    console.error(`skills/ directory not found at ${skillsDir}`);
    process.exit(1);
  }

  const skills = fs.readdirSync(skillsDir)
    .filter(f => f.endsWith('.json'))
    .map(f => path.join(skillsDir, f));

  if (skills.length === 0) {
    console.warn('WARNING: No skill definitions found (*.json)');
    process.exit(0);
  }

  console.log(`Validating ${skills.length} skill definition(s)...`);
  let allValid = true;
  for (const skill of skills) {
    if (!validateSkill(skill)) {
      allValid = false;
    }
  }

  if (allValid) {
    console.log(`\nAll ${skills.length} skill definition(s) are valid.`);
    process.exit(0);
  } else {
    console.error('\nSkill validation FAILED. Fix errors above and retry.');
    process.exit(1);
  }
}

main();
