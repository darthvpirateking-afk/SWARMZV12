/**
 * Plugin validation script
 * Usage: node dist/cli/plugin-validate.js
 */

import * as fs from 'fs';
import * as path from 'path';
import { PluginManifest } from './types';

const REQUIRED_FIELDS: (keyof PluginManifest)[] = [
  'name',
  'version',
  'description',
  'author',
  'category',
  'capabilities',
  'entry',
  'tags',
  'marketplace',
];

const VALID_CATEGORIES = ['data', 'filesystem', 'communication', 'ai', 'integration'];

function validateManifest(manifest: unknown, filePath: string): string[] {
  const errors: string[] = [];

  if (typeof manifest !== 'object' || manifest === null) {
    return [`${filePath}: manifest must be a JSON object`];
  }

  const m = manifest as Record<string, unknown>;

  for (const field of REQUIRED_FIELDS) {
    if (m[field] === undefined) {
      errors.push(`${filePath}: missing required field "${field}"`);
    }
  }

  if (m.name && typeof m.name !== 'string') {
    errors.push(`${filePath}: "name" must be a string`);
  }

  if (m.version && typeof m.version !== 'string') {
    errors.push(`${filePath}: "version" must be a string`);
  }

  if (m.category && !VALID_CATEGORIES.includes(m.category as string)) {
    errors.push(
      `${filePath}: "category" must be one of: ${VALID_CATEGORIES.join(', ')}`
    );
  }

  if (m.capabilities && !Array.isArray(m.capabilities)) {
    errors.push(`${filePath}: "capabilities" must be an array`);
  }

  if (m.tags && !Array.isArray(m.tags)) {
    errors.push(`${filePath}: "tags" must be an array`);
  }

  if (m.marketplace && typeof m.marketplace === 'object') {
    const mp = m.marketplace as Record<string, unknown>;
    if (!mp.title) errors.push(`${filePath}: "marketplace.title" is required`);
    if (!mp.icon) errors.push(`${filePath}: "marketplace.icon" is required`);
    if (mp.price && !['free', 'paid'].includes(mp.price as string)) {
      errors.push(`${filePath}: "marketplace.price" must be "free" or "paid"`);
    }
  }

  return errors;
}

function run(): void {
  const manifestsDir = path.resolve(process.cwd(), 'plugins', 'manifests');

  if (!fs.existsSync(manifestsDir)) {
    console.error(`Manifests directory not found: ${manifestsDir}`);
    process.exit(1);
  }

  const files = fs
    .readdirSync(manifestsDir)
    .filter((f) => f.endsWith('.manifest.json'));

  if (files.length === 0) {
    console.log('No plugin manifests found.');
    process.exit(0);
  }

  let totalErrors = 0;

  for (const file of files) {
    const filePath = path.join(manifestsDir, file);
    let manifest: unknown;

    try {
      manifest = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (e) {
      console.error(`✗ ${file}: invalid JSON - ${(e as Error).message}`);
      totalErrors++;
      continue;
    }

    const errors = validateManifest(manifest, file);
    if (errors.length === 0) {
      console.log(`✓ ${file}`);
    } else {
      errors.forEach((err) => console.error(`✗ ${err}`));
      totalErrors += errors.length;
    }
  }

  console.log(`\nValidated ${files.length} manifest(s). ${totalErrors} error(s).`);
  if (totalErrors > 0) process.exit(1);
}

run();
