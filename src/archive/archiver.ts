/**
 * Archiver - Persists artifact packs to ./packs/ directory
 * Part of Archive Layer - saves completed artifacts for later retrieval
 */

import * as fs from 'fs';
import * as path from 'path';
import { ArtifactPack } from '../types';

export class Archiver {
  private packsDir: string;

  constructor(packsDir: string = './packs') {
    this.packsDir = packsDir;
  }

  /**
   * Ensure the packs directory exists
   */
  ensurePacksDir(): void {
    if (!fs.existsSync(this.packsDir)) {
      fs.mkdirSync(this.packsDir, { recursive: true });
    }
  }

  /**
   * Save an artifact pack to disk as JSON
   */
  save(pack: ArtifactPack): string {
    this.ensurePacksDir();
    const filename = `${pack.id}.json`;
    const filepath = path.join(this.packsDir, filename);
    fs.writeFileSync(filepath, JSON.stringify(pack, null, 2), 'utf-8');
    return filepath;
  }

  /**
   * Load an artifact pack by ID
   */
  load(packId: string): ArtifactPack | null {
    const filepath = path.join(this.packsDir, `${packId}.json`);
    if (!fs.existsSync(filepath)) {
      return null;
    }
    const content = fs.readFileSync(filepath, 'utf-8');
    return JSON.parse(content) as ArtifactPack;
  }

  /**
   * List all archived pack IDs
   */
  list(): string[] {
    if (!fs.existsSync(this.packsDir)) {
      return [];
    }
    return fs.readdirSync(this.packsDir)
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace('.json', ''));
  }

  /**
   * Get the packs directory path
   */
  getPacksDir(): string {
    return this.packsDir;
  }
}
