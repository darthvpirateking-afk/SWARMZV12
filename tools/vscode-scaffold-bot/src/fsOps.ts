import * as fs from "fs";
import * as path from "path";
import { renderString } from "./render";
import { TemplateManifest } from "./templateRegistry";

export interface GenerationResult {
  conflicts: string[];
  createdFiles: string[];
  error?: string;
  skippedFiles: string[];
  status: "ok" | "fail";
}

function collectFiles(dir: string, base: string = ""): string[] {
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const rel = path.join(base, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectFiles(path.join(dir, entry.name), rel));
    } else {
      files.push(rel);
    }
  }
  return files;
}

function applyRenames(
  relPath: string,
  renames: Array<{ from: string; to: string }> | undefined
): string {
  if (!renames) {
    return relPath;
  }
  for (const rename of renames) {
    const from = rename.from.replace(/^files\//, "");
    const to = rename.to.replace(/^files\//, "");
    if (relPath === from) {
      return to;
    }
  }
  return relPath;
}

export function generateFiles(
  filesDir: string,
  targetDir: string,
  vars: Record<string, string>,
  manifest: TemplateManifest,
  allowOverwrite: boolean = false,
  dryRun: boolean = false
): GenerationResult {
  const result: GenerationResult = {
    conflicts: [],
    createdFiles: [],
    skippedFiles: [],
    status: "ok",
  };

  try {
    const outputPath = renderString(manifest.output.path, vars);
    const outputDir = path.join(targetDir, manifest.output.root || ".", outputPath);
    const conflictMode = manifest.output.conflict || "fail";

    if (fs.existsSync(outputDir) && conflictMode === "fail") {
      result.conflicts.push(outputDir);
      result.error = `Output directory already exists: ${outputDir}`;
      result.status = "fail";
      return result;
    }
    if (fs.existsSync(outputDir) && conflictMode === "skip") {
      result.skippedFiles.push(outputDir);
      return result;
    }

    const templateFiles = collectFiles(filesDir);
    for (const relPath of templateFiles) {
      const renamedPath = applyRenames(relPath, manifest.renames);
      const renderedPath = renderString(renamedPath, vars);
      const destPath = path.join(outputDir, renderedPath);
      if (fs.existsSync(destPath) && conflictMode === "merge" && !allowOverwrite) {
        result.skippedFiles.push(renderedPath);
        continue;
      }
      if (fs.existsSync(destPath) && conflictMode === "fail") {
        result.conflicts.push(renderedPath);
        result.error = `Conflict detected for file: ${renderedPath}`;
        result.status = "fail";
        return result;
      }
      if (!dryRun) {
        fs.mkdirSync(path.dirname(destPath), { recursive: true });
        const content = fs.readFileSync(path.join(filesDir, relPath), "utf-8");
        fs.writeFileSync(destPath, renderString(content, vars), "utf-8");
      }
      result.createdFiles.push(renderedPath);
    }
  } catch (err) {
    result.error = err instanceof Error ? err.message : String(err);
    result.status = "fail";
  }

  return result;
}
