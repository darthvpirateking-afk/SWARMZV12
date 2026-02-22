/**
 * Skill validation script
 * Usage: node dist/cli/skill-validate.js
 */

import * as fs from 'fs';
import * as path from 'path';
import { SkillManifest } from './types';

const REQUIRED_FIELDS: (keyof SkillManifest)[] = [
  'name',
  'version',
  'description',
  'agent',
  'triggers',
  'actions',
  'tags',
];

function validateSkill(manifest: unknown, filePath: string): string[] {
  const errors: string[] = [];

  if (typeof manifest !== 'object' || manifest === null) {
    return [`${filePath}: skill must be a JSON object`];
  }

  const m = manifest as Record<string, unknown>;

  for (const field of REQUIRED_FIELDS) {
    if (m[field] === undefined) {
      errors.push(`${filePath}: missing required field "${field}"`);
    }
  }

  if (m.triggers && !Array.isArray(m.triggers)) {
    errors.push(`${filePath}: "triggers" must be an array`);
  }

  if (m.triggers && Array.isArray(m.triggers) && m.triggers.length === 0) {
    errors.push(`${filePath}: "triggers" must have at least one entry`);
  }

  if (m.actions && !Array.isArray(m.actions)) {
    errors.push(`${filePath}: "actions" must be an array`);
  }

  if (m.actions && Array.isArray(m.actions)) {
    (m.actions as unknown[]).forEach((action, i) => {
      if (typeof action !== 'object' || action === null) {
        errors.push(`${filePath}: actions[${i}] must be an object`);
        return;
      }
      const a = action as Record<string, unknown>;
      if (!a.id) errors.push(`${filePath}: actions[${i}].id is required`);
      if (!a.type) errors.push(`${filePath}: actions[${i}].type is required`);
    });
  }

  return errors;
}

function run(): void {
  const skillsDir = path.resolve(process.cwd(), 'skills');

  if (!fs.existsSync(skillsDir)) {
    console.error(`Skills directory not found: ${skillsDir}`);
    process.exit(1);
  }

  const files = fs
    .readdirSync(skillsDir)
    .filter((f) => f.endsWith('.json'));

  if (files.length === 0) {
    console.log('No skill definitions found.');
    process.exit(0);
  }

  let totalErrors = 0;

  for (const file of files) {
    const filePath = path.join(skillsDir, file);
    let skill: unknown;

    try {
      skill = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
      console.error(`✗ ${file}: invalid JSON - ${(e as Error).message}`);
      totalErrors++;
      continue;
    }

    const errors = validateSkill(skill, file);
    if (errors.length === 0) {
      console.log(`✓ ${file}`);
    } else {
      errors.forEach((err) => console.error(`✗ ${err}`));
      totalErrors += errors.length;
    }
  }

  console.log(`\nValidated ${files.length} skill(s). ${totalErrors} error(s).`);
  if (totalErrors > 0) process.exit(1);
}

run();
