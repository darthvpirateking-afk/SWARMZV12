/**
 * Create a new skill definition scaffold
 * Usage: node dist/cli/skill-create.js --name <skill-name>
 */

import * as fs from 'fs';
import * as path from 'path';
import { SkillManifest } from './types';

function parseName(): string {
  const args = process.argv.slice(2);
  const idx = args.indexOf('--name');
  if (idx === -1 || !args[idx + 1]) {
    console.error('Usage: npm run skill:create -- --name <skill-name>');
    process.exit(1);
  }
  return args[idx + 1].toLowerCase().replace(/\s+/g, '-');
}

function run(): void {
  const name = parseName();
  const skillsDir = path.resolve(process.cwd(), 'skills');

  if (!fs.existsSync(skillsDir)) {
    fs.mkdirSync(skillsDir, { recursive: true });
  }

  const outputPath = path.join(skillsDir, `${name}.json`);

  if (fs.existsSync(outputPath)) {
    console.error(`Skill already exists: ${outputPath}`);
    process.exit(1);
  }

  const skill: SkillManifest = {
    name,
    version: '1.0.0',
    description: `${name} skill for SWARMZ agents`,
    agent: 'nexusmon',
    triggers: [name.replace(/-/g, ' ')],
    actions: [
      {
        id: 'execute',
        type: 'generic',
        config: {},
      },
    ],
    tags: [name],
  };

  fs.writeFileSync(outputPath, JSON.stringify(skill, null, 2));
  console.log(`Created skill: ${outputPath}`);
  console.log(`Next: add triggers and actions to ${name}.json`);
}

run();
