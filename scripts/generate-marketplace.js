#!/usr/bin/env node
/**
 * Marketplace Generator
 * Reads plugin manifests and skill definitions to generate marketplace.json.
 * Also appends a marketplace summary section to the README.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const pluginsDir = path.join(ROOT, 'plugins');
const skillsDir = path.join(ROOT, 'skills');
const outFile = path.join(ROOT, 'marketplace.json');
const readmeFile = path.join(ROOT, 'README.md');

function loadPlugins() {
  if (!fs.existsSync(pluginsDir)) return [];
  let hasError = false;
  const results = fs.readdirSync(pluginsDir)
    .filter(f => f.endsWith('.manifest.json'))
    .map(f => {
      const filePath = path.join(pluginsDir, f);
      try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
      } catch (err) {
        console.error(`ERROR: Could not parse ${path.relative(process.cwd(), filePath)}: ${err.message}`);
        hasError = true;
        return null;
      }
    })
    .filter(Boolean);
  if (hasError) {
    console.error('Aborting marketplace generation due to plugin manifest parse errors.');
    process.exit(1);
  }
  return results;
}

function loadSkills() {
  if (!fs.existsSync(skillsDir)) return [];
  let hasError = false;
  const results = fs.readdirSync(skillsDir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      const filePath = path.join(skillsDir, f);
      try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
      } catch (err) {
        console.error(`ERROR: Could not parse ${path.relative(process.cwd(), filePath)}: ${err.message}`);
        hasError = true;
        return null;
      }
    })
    .filter(Boolean);
  if (hasError) {
    console.error('Aborting marketplace generation due to skill definition parse errors.');
    process.exit(1);
  }
  return results;
}

function getGeneratedAt() {
  const epoch = process.env.SOURCE_DATE_EPOCH;
  if (epoch) {
    const parsed = Number(epoch);
    if (Number.isFinite(parsed)) {
      return new Date(parsed * 1000).toISOString();
    }
  }
  return new Date().toISOString();
}

function generateMarketplace(plugins, skills) {
  return {
    version: '1.0.0',
    generated_at: getGeneratedAt(),
    plugins: plugins.map(p => ({
      name: p.name,
      version: p.version,
      description: p.description,
      category: p.category,
      capabilities: p.capabilities,
      entry_point: p.entry_point,
    })),
    skills: skills.map(s => ({
      name: s.name,
      version: s.version,
      description: s.description,
      category: s.category,
      tags: s.tags || [],
    })),
  };
}

function updateReadme(marketplace) {
  if (!fs.existsSync(readmeFile)) return;

  const readme = fs.readFileSync(readmeFile, 'utf8');
  const marker = '<!-- MARKETPLACE_START -->';
  const endMarker = '<!-- MARKETPLACE_END -->';

  const pluginRows = marketplace.plugins
    .map(p => `| ${p.name} | ${p.version} | ${p.category} | ${p.description} |`)
    .join('\n');

  const skillRows = marketplace.skills
    .map(s => `| ${s.name} | ${s.version} | ${s.category} | ${s.description} |`)
    .join('\n');

  const section = `${marker}
## Marketplace

### Plugins (${marketplace.plugins.length})

| Name | Version | Category | Description |
|------|---------|----------|-------------|
${pluginRows}

### Skills (${marketplace.skills.length})

| Name | Version | Category | Description |
|------|---------|----------|-------------|
${skillRows}
${endMarker}`;

  let updated;
  if (readme.includes(marker) && readme.includes(endMarker)) {
    updated = readme.replace(
      new RegExp(`${marker}[\\s\\S]*?${endMarker}`),
      section
    );
  } else {
    updated = readme + '\n\n' + section + '\n';
  }

  fs.writeFileSync(readmeFile, updated, 'utf8');
  console.log('  README.md updated with marketplace section.');
}

function main() {
  const plugins = loadPlugins();
  const skills = loadSkills();
  const marketplace = generateMarketplace(plugins, skills);

  fs.writeFileSync(outFile, JSON.stringify(marketplace, null, 2), 'utf8');
  console.log(`Generated marketplace.json with ${plugins.length} plugin(s) and ${skills.length} skill(s).`);

  updateReadme(marketplace);
}

main();
