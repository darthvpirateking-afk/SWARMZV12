/**
 * File system operations for scaffold generation.
 * Handles recursive file tree creation with conflict handling.
 */

import * as path from "path";
import * as fs from "fs";
import { renderString } from "./render";
import { TemplateManifest } from "./templateRegistry";

export interface GenerationResult {
  createdFiles: string[];
  skippedFiles: string[];
  conflicts: string[];
  status: "ok" | "fail";
  error?: string;
}

/**
 * Collect all file paths from a template's files/ directory (recursively).
 * Returns relative paths from the filesDir root.
 */
function collectFiles(dir: string, base: string = ""): string[] {
  const results: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const rel = path.join(base, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(path.join(dir, entry.name), rel));
    } else {
      results.push(rel);
    }
  }
  return results;
}

/**
 * Apply renames from template.json.
 * Renames are applied to relative paths within files/ directory.
 */
function applyRenames(
  relPath: string,
  renames: Array<{ from: string; to: string }> | undefined
): string {
  if (!renames) {
    return relPath;
  }
  for (const r of renames) {
    // Strip the "files/" prefix from rename paths for matching
    const from = r.from.replace(/^files\//, "");
    const to = r.to.replace(/^files\//, "");
    if (relPath === from) {
      return to;
    }
  }
  return relPath;
}

/**
 * Generate files from a template into a target directory.
 *
 * @param filesDir Absolute path to the template's files/ directory
 * @param targetDir Absolute path to the output directory
 * @param vars Resolved placeholder variables
 * @param manifest The template manifest
 * @param allowOverwrite Whether to overwrite existing files during merge
 * @param dryRun If true, don't actually write files
 */
export function generateFiles(
  filesDir: string,
  targetDir: string,
  vars: Record<string, string>,
  manifest: TemplateManifest,
  allowOverwrite: boolean = false,
  dryRun: boolean = false
): GenerationResult {
  const result: GenerationResult = {
    createdFiles: [],
    skippedFiles: [],
    conflicts: [],
    status: "ok",
  };

  try {
    // Resolve output path
    const outputSubPath = renderString(manifest.output.path, vars);
    const outputDir = path.join(targetDir, manifest.output.root || ".", outputSubPath);

    const conflict = manifest.output.conflict || "fail";

    // Check if output directory exists
    if (fs.existsSync(outputDir)) {
      if (conflict === "fail") {
        result.status = "fail";
        result.error = `Output directory already exists: ${outputDir}`;
        result.conflicts.push(outputDir);
        return result;
      }
      if (conflict === "skip") {
        result.status = "ok";
        result.skippedFiles.push(outputDir);
        return result;
      }
      // conflict === "merge": continue, create missing files only
    }

    // Collect template files
    const templateFiles = collectFiles(filesDir);

    for (const relPath of templateFiles) {
      // Apply renames
      const renamedPath = applyRenames(relPath, manifest.renames);
      // Render placeholders in the path
      const renderedPath = renderString(renamedPath, vars);
      const destPath = path.join(outputDir, renderedPath);

      // Check for conflicts
      if (fs.existsSync(destPath)) {
        if (conflict === "merge" && !allowOverwrite) {
          result.skippedFiles.push(renderedPath);
          continue;
        }
        result.conflicts.push(renderedPath);
      }

      if (!dryRun) {
        // Ensure parent directory exists
        const parentDir = path.dirname(destPath);
        fs.mkdirSync(parentDir, { recursive: true });

        // Read source file and render placeholders in content
        const srcPath = path.join(filesDir, relPath);
        const content = fs.readFileSync(srcPath, "utf-8");
        const renderedContent = renderString(content, vars);
        fs.writeFileSync(destPath, renderedContent, "utf-8");
      }

      result.createdFiles.push(renderedPath);
    }
  } catch (err) {
    result.status = "fail";
    result.error = err instanceof Error ? err.message : String(err);
  }

  return result;
}
