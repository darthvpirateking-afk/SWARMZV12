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
