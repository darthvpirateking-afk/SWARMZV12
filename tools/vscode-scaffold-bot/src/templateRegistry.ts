import * as fs from "fs";
import * as path from "path";

export interface VariableDef {
  default?: string;
  key: string;
  pattern?: string;
  prompt: string;
  transform?: "lower" | "upper" | "snake" | "kebab" | "pascal";
}

export interface TemplateManifest {
  description: string;
  id: string;
  output: {
    conflict: "fail" | "skip" | "merge";
    path: string;
    root: string;
  };
  renames?: Array<{ from: string; to: string }>;
  title: string;
  variables: VariableDef[];
  version: number;
}

export interface TemplateEntry {
  filesDir: string;
  manifest: TemplateManifest;
  source: "repo" | "bundled";
}

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
    for (const variable of m.variables) {
      if (typeof variable !== "object" || variable === null) {
        errors.push("Each variable must be an object");
        continue;
      }
      if (typeof variable.key !== "string" || variable.key.length === 0) {
        errors.push("Variable missing 'key'");
      }
      if (typeof variable.prompt !== "string") {
        errors.push(`Variable '${String(variable.key)}' missing 'prompt'`);
      }
    }
  }
  if (typeof m.output !== "object" || m.output === null) {
    errors.push("Missing 'output' object");
  } else {
    const output = m.output as Record<string, unknown>;
    if (typeof output.path !== "string") {
      errors.push("output.path must be a string");
    }
    if (!["fail", "skip", "merge"].includes(String(output.conflict))) {
      errors.push("output.conflict must be 'fail', 'skip', or 'merge'");
    }
  }
  return errors;
}

function scanTemplatesDir(dir: string, source: "repo" | "bundled"): TemplateEntry[] {
  const entries: TemplateEntry[] = [];
  if (!fs.existsSync(dir)) {
    return entries;
  }
  for (const name of fs.readdirSync(dir)) {
    const templateDir = path.join(dir, name);
    const manifestPath = path.join(templateDir, "template.json");
    const filesDir = path.join(templateDir, "files");
    if (!fs.existsSync(manifestPath) || !fs.existsSync(filesDir)) {
      continue;
    }
    try {
      const raw = fs.readFileSync(manifestPath, "utf-8");
      const manifest = JSON.parse(raw) as TemplateManifest;
      if (validateManifest(manifest).length === 0) {
        entries.push({ filesDir, manifest, source });
      }
    } catch {
      // Skip malformed templates.
    }
  }
  return entries;
}

export function discoverTemplates(
  repoTemplatesDir: string,
  bundledTemplatesDir: string,
  preferRepo: boolean = true
): TemplateEntry[] {
  const repoEntries = scanTemplatesDir(repoTemplatesDir, "repo");
  const bundledEntries = scanTemplatesDir(bundledTemplatesDir, "bundled");
  const seen = new Map<string, TemplateEntry>();

  if (preferRepo) {
    for (const entry of repoEntries) {
      seen.set(entry.manifest.id, entry);
    }
    for (const entry of bundledEntries) {
      if (!seen.has(entry.manifest.id)) {
        seen.set(entry.manifest.id, entry);
      }
    }
  } else {
    for (const entry of bundledEntries) {
      seen.set(entry.manifest.id, entry);
    }
    for (const entry of repoEntries) {
      if (!seen.has(entry.manifest.id)) {
        seen.set(entry.manifest.id, entry);
      }
    }
  }

  return Array.from(seen.values());
}
