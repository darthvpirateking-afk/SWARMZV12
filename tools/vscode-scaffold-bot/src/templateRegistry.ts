/**
 * Template discovery and loading.
 * Searches repo-level templates first, then falls back to bundled templates.
 */

import * as path from "path";
import * as fs from "fs";

export interface VariableDef {
  key: string;
  prompt: string;
  default?: string;
  pattern?: string;
  transform?: "lower" | "upper" | "snake" | "kebab" | "pascal";
}

export interface TemplateManifest {
  id: string;
  title: string;
  description: string;
  version: number;
  variables: VariableDef[];
  output: {
    root: string;
    path: string;
    conflict: "fail" | "skip" | "merge";
  };
  renames?: Array<{ from: string; to: string }>;
}

export interface TemplateEntry {
  manifest: TemplateManifest;
  filesDir: string;
  source: "repo" | "bundled";
}

/** Validate a template.json manifest and return errors (empty array = valid) */
export function validateManifest(obj: unknown): string[] {
  const errors: string[] = [];
  if (typeof obj !== "object" || obj === null) {
    return ["Manifest must be a JSON object"];
  }
  const m = obj as Record<string, unknown>;

  if (typeof m.id !== "string" || m.id.length === 0) {
    errors.push("Missing or empty 'id'");
  }
  if (typeof m.title !== "string" || m.title.length === 0) {
    errors.push("Missing or empty 'title'");
  }
  if (typeof m.description !== "string") {
    errors.push("Missing 'description'");
  }
  if (typeof m.version !== "number" || !Number.isInteger(m.version)) {
    errors.push("'version' must be an integer");
  }
  if (!Array.isArray(m.variables)) {
    errors.push("'variables' must be an array");
  } else {
    for (const v of m.variables) {
      if (typeof v !== "object" || v === null) {
        errors.push("Each variable must be an object");
        continue;
      }
      if (typeof v.key !== "string" || v.key.length === 0) {
        errors.push("Variable missing 'key'");
      }
      if (typeof v.prompt !== "string") {
        errors.push(`Variable '${v.key}' missing 'prompt'`);
      }
    }
  }
  if (typeof m.output !== "object" || m.output === null) {
    errors.push("Missing 'output' object");
  } else {
    const out = m.output as Record<string, unknown>;
    if (typeof out.path !== "string") {
      errors.push("output.path must be a string");
    }
    if (!["fail", "skip", "merge"].includes(out.conflict as string)) {
      errors.push("output.conflict must be 'fail', 'skip', or 'merge'");
    }
  }

  return errors;
}

/** Scan a directory for template sub-folders (each must have template.json + files/) */
function scanTemplatesDir(dir: string, source: "repo" | "bundled"): TemplateEntry[] {
  const entries: TemplateEntry[] = [];
  if (!fs.existsSync(dir)) {
    return entries;
  }
  for (const name of fs.readdirSync(dir)) {
    const tplDir = path.join(dir, name);
    const manifestPath = path.join(tplDir, "template.json");
    const filesDir = path.join(tplDir, "files");
    if (!fs.existsSync(manifestPath) || !fs.existsSync(filesDir)) {
      continue;
    }
    try {
      const raw = fs.readFileSync(manifestPath, "utf-8");
      const manifest = JSON.parse(raw) as TemplateManifest;
      const errs = validateManifest(manifest);
      if (errs.length === 0) {
        entries.push({ manifest, filesDir, source });
      }
    } catch {
      // Skip malformed templates
    }
  }
  return entries;
}

/**
 * Discover all templates, preferring repo-level over bundled.
 * @param repoTemplatesDir Absolute path to repo templates (.swarmz/templates)
 * @param bundledTemplatesDir Absolute path to bundled templates
 * @param preferRepo Whether to prefer repo templates when IDs collide
 */
export function discoverTemplates(
  repoTemplatesDir: string,
  bundledTemplatesDir: string,
  preferRepo: boolean = true
): TemplateEntry[] {
  const repoEntries = scanTemplatesDir(repoTemplatesDir, "repo");
  const bundledEntries = scanTemplatesDir(bundledTemplatesDir, "bundled");

  const seen = new Map<string, TemplateEntry>();

  if (preferRepo) {
    for (const e of repoEntries) {
      seen.set(e.manifest.id, e);
    }
    for (const e of bundledEntries) {
      if (!seen.has(e.manifest.id)) {
        seen.set(e.manifest.id, e);
      }
    }
  } else {
    for (const e of bundledEntries) {
      seen.set(e.manifest.id, e);
    }
    for (const e of repoEntries) {
      if (!seen.has(e.manifest.id)) {
        seen.set(e.manifest.id, e);
      }
    }
  }

  return Array.from(seen.values());
import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";

export interface TemplateMeta {
  id: string;
  title: string;
  description: string;
  version: string;
  variables: TemplateVariable[];
  source: "bundled" | "repo";
  dir: string;
}

export interface TemplateVariable {
  name: string;
  prompt: string;
  default?: string;
}

function getConfig<T>(key: string): T {
  return vscode.workspace.getConfiguration("scaffoldBot").get<T>(key) as T;
}

function bundledTemplatesDir(): string {
  return path.join(__dirname, "..", "templates");
}

function repoTemplatesDir(): vscode.Uri | null {
  const ws = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (!ws) return null;
  const rel = getConfig<string>("templatesPath") || ".swarmz/templates";
  return vscode.Uri.joinPath(ws, rel);
}

async function scanDir(dir: string, source: "bundled" | "repo"): Promise<TemplateMeta[]> {
  const results: TemplateMeta[] = [];
  if (!fs.existsSync(dir)) return results;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const tplPath = path.join(dir, entry.name, "template.json");
    if (!fs.existsSync(tplPath)) continue;
    try {
      const raw = JSON.parse(fs.readFileSync(tplPath, "utf-8"));
      results.push({
        id: raw.id ?? entry.name,
        title: raw.title ?? entry.name,
        description: raw.description ?? "",
        version: raw.version ?? "0.0.0",
        variables: raw.variables ?? [],
        source,
        dir: path.join(dir, entry.name),
      });
    } catch {
      // skip invalid template.json
    }
  }
  return results;
}

export async function listTemplates(): Promise<TemplateMeta[]> {
  const preferRepo = getConfig<boolean>("preferRepoTemplates");
  const bundled = await scanDir(bundledTemplatesDir(), "bundled");

  const repoUri = repoTemplatesDir();
  const repo = repoUri ? await scanDir(repoUri.fsPath, "repo") : [];

  if (preferRepo) {
    const repoIds = new Set(repo.map(t => t.id));
    return [...repo, ...bundled.filter(t => !repoIds.has(t.id))];
  }
  const bundledIds = new Set(bundled.map(t => t.id));
  return [...bundled, ...repo.filter(t => !bundledIds.has(t.id))];
}

export async function loadTemplate(id: string): Promise<TemplateMeta | null> {
  const all = await listTemplates();
  return all.find(t => t.id === id) ?? null;
}
