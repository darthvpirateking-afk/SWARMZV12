/**
 * Generate marketplace.json from plugin manifests
 * Usage: node dist/cli/plugin-generate-marketplace.js
 */

import * as fs from 'fs';
import * as path from 'path';
import { PluginManifest, Marketplace } from './types';

function run(): void {
  const manifestsDir = path.resolve(process.cwd(), 'plugins', 'manifests');
  const outputPath = path.resolve(process.cwd(), 'marketplace.json');

  if (!fs.existsSync(manifestsDir)) {
    console.error(`Manifests directory not found: ${manifestsDir}`);
    process.exit(1);
  }

  const files = fs
    .readdirSync(manifestsDir)
    .filter((f) => f.endsWith('.manifest.json'));

  const plugins = files.map((file) => {
    const filePath = path.join(manifestsDir, file);
    const manifest: PluginManifest = JSON.parse(fs.readFileSync(filePath, 'utf8'));

    return {
      name: manifest.name,
      version: manifest.version,
      title: manifest.marketplace.title,
      description: manifest.description,
      category: manifest.category,
      icon: manifest.marketplace.icon,
      price: manifest.marketplace.price,
      tags: manifest.tags,
      capabilities: manifest.capabilities,
    };
  });

  const marketplace: Marketplace = {
    generated_at: new Date().toISOString(),
    total: plugins.length,
    plugins,
  };

  fs.writeFileSync(outputPath, JSON.stringify(marketplace, null, 2));
  console.log(`Generated marketplace.json with ${plugins.length} plugin(s).`);
}

run();
