#!/usr/bin/env node
/**
 * Plugin Manifest Validator
 * Validates all plugin manifest JSON files in the plugins/ directory.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const REQUIRED_FIELDS = ['name', 'version', 'description', 'entry_point', 'capabilities', 'category'];

const pluginsDir = path.resolve(__dirname, '..', 'plugins');

function validateManifest(filePath) {
  const rel = path.relative(process.cwd(), filePath);
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    console.error(`  ERROR: Could not parse ${rel}: ${err.message}`);
    return false;
  }

  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    console.error(`  ERROR: ${rel} must contain a JSON object at the top level`);
    return false;
  }

  let valid = true;
  for (const field of REQUIRED_FIELDS) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      console.error(`  ERROR: ${rel} missing required field: "${field}"`);
      valid = false;
    }
  }

  if (!Array.isArray(data.capabilities) || data.capabilities.length === 0) {
    console.error(`  ERROR: ${rel} - "capabilities" must be a non-empty array`);
    valid = false;
  }

  const entryPath = path.resolve(pluginsDir, data.entry_point || '');
  if (data.entry_point && !fs.existsSync(entryPath)) {
    console.error(`  ERROR: ${rel} - entry_point "${data.entry_point}" not found`);
    valid = false;
  }

  if (valid) {
    console.log(`  OK: ${rel} (${data.name}@${data.version})`);
  }
  return valid;
}

function main() {
  if (!fs.existsSync(pluginsDir)) {
    console.error(`plugins/ directory not found at ${pluginsDir}`);
    process.exit(1);
  }

  const manifests = fs.readdirSync(pluginsDir)
    .filter(f => f.endsWith('.manifest.json'))
    .map(f => path.join(pluginsDir, f));

  if (manifests.length === 0) {
    console.warn('WARNING: No plugin manifests found (*.manifest.json)');
    process.exit(0);
  }

  console.log(`Validating ${manifests.length} plugin manifest(s)...`);
  let allValid = true;
  for (const manifest of manifests) {
    if (!validateManifest(manifest)) {
      allValid = false;
    }
  }

  if (allValid) {
    console.log(`\nAll ${manifests.length} plugin manifest(s) are valid.`);
    process.exit(0);
  } else {
    console.error('\nPlugin validation FAILED. Fix errors above and retry.');
    process.exit(1);
  }
}

main();
