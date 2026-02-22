/**
 * Create a new plugin manifest scaffold
 * Usage: node dist/cli/plugin-create.js --name <plugin-name>
 */

import * as fs from 'fs';
import * as path from 'path';
import { PluginManifest } from './types';

function parseName(): string {
  const args = process.argv.slice(2);
  const idx = args.indexOf('--name');
  if (idx === -1 || !args[idx + 1]) {
    console.error('Usage: npm run plugin:create -- --name <plugin-name>');
    process.exit(1);
  }
  return args[idx + 1].toLowerCase().replace(/\s+/g, '-');
}

function run(): void {
  const name = parseName();
  const manifestsDir = path.resolve(process.cwd(), 'plugins', 'manifests');

  if (!fs.existsSync(manifestsDir)) {
    fs.mkdirSync(manifestsDir, { recursive: true });
  }

  const outputPath = path.join(manifestsDir, `${name}.manifest.json`);

  if (fs.existsSync(outputPath)) {
    console.error(`Plugin manifest already exists: ${outputPath}`);
    process.exit(1);
  }

  const manifest: PluginManifest = {
    name,
    version: '1.0.0',
    description: `${name} plugin for SWARMZ`,
    author: 'SWARMZ',
    category: 'ai',
    capabilities: [],
    entry: `plugins/${name}.py`,
    tags: [name],
    marketplace: {
      title: name
        .split('-')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' '),
      icon: '🔌',
      price: 'free',
    },
  };

  fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2));
  console.log(`Created plugin manifest: ${outputPath}`);
  console.log(`Next: add capabilities to ${name}.manifest.json and create plugins/${name}.py`);
}

run();
