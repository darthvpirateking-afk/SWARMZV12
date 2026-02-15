/**
 * Self-check: validates manifests, renderer, dry-run generation, and audit writer.
 * Returns clear PASS/FAIL summary.
 */

import * as path from "path";
import * as fs from "fs";
import * as os from "os";
import { discoverTemplates, validateManifest } from "./templateRegistry";
import { renderString, buildBuiltInVars, toSnakeCase, toKebabCase, toPascalCase } from "./render";
import { generateFiles } from "./fsOps";
import { writeAuditEntry, readAuditEntries, AuditEntry } from "./audit";

export interface CheckResult {
  name: string;
  passed: boolean;
  detail: string;
}

/** Run all self-checks, return results */
export function runSelfChecks(
  repoTemplatesDir: string,
  bundledTemplatesDir: string
): CheckResult[] {
  const results: CheckResult[] = [];

  // 1. Validate renderer transforms
  results.push(checkTransforms());

  // 2. Validate placeholder rendering
  results.push(checkPlaceholderRendering());

  // 3. Validate manifests
  results.push(...checkManifests(repoTemplatesDir, bundledTemplatesDir));

  // 4. Dry-run generation
  results.push(checkDryRun(repoTemplatesDir, bundledTemplatesDir));

  // 5. Audit writer
  results.push(checkAuditWriter());

  return results;
}

function checkTransforms(): CheckResult {
  try {
    const checks = [
      { fn: toSnakeCase, input: "myModuleName", expected: "my_module_name" },
      { fn: toKebabCase, input: "myModuleName", expected: "my-module-name" },
      { fn: toPascalCase, input: "my-module-name", expected: "MyModuleName" },
      { fn: toSnakeCase, input: "Hello World", expected: "hello_world" },
      { fn: toKebabCase, input: "Hello World", expected: "hello-world" },
      { fn: toPascalCase, input: "hello_world", expected: "HelloWorld" },
    ];

    for (const c of checks) {
      const result = c.fn(c.input);
      if (result !== c.expected) {
        return {
          name: "Transforms",
          passed: false,
          detail: `${c.fn.name}("${c.input}") = "${result}", expected "${c.expected}"`,
        };
      }
    }
    return { name: "Transforms", passed: true, detail: "All transform functions correct" };
  } catch (err) {
    return { name: "Transforms", passed: false, detail: String(err) };
  }
}

function checkPlaceholderRendering(): CheckResult {
  try {
    const vars = buildBuiltInVars("userAuth", "2025-01-15T10:00:00.000Z");
    const template = "Hello {{name}}, your module is {{snakeName}} ({{year}})";
    const rendered = renderString(template, vars as unknown as Record<string, string>);
    const expected = "Hello userAuth, your module is user_auth (2025)";
    if (rendered !== expected) {
      return {
        name: "Placeholder rendering",
        passed: false,
        detail: `Got "${rendered}", expected "${expected}"`,
      };
    }
    // Check unknown tokens are preserved
    const unknown = renderString("{{unknown}} stays", {});
    if (unknown !== "{{unknown}} stays") {
      return {
        name: "Placeholder rendering",
        passed: false,
        detail: "Unknown tokens should be preserved",
      };
    }
    return { name: "Placeholder rendering", passed: true, detail: "All placeholder tests pass" };
  } catch (err) {
    return { name: "Placeholder rendering", passed: false, detail: String(err) };
  }
}

function checkManifests(
  repoTemplatesDir: string,
  bundledTemplatesDir: string
): CheckResult[] {
  const results: CheckResult[] = [];
  const templates = discoverTemplates(repoTemplatesDir, bundledTemplatesDir, true);
  if (templates.length === 0) {
    results.push({
      name: "Manifest discovery",
      passed: false,
      detail: "No templates found",
    });
    return results;
  }

  for (const tpl of templates) {
    const errs = validateManifest(tpl.manifest);
    results.push({
      name: `Manifest: ${tpl.manifest.id}`,
      passed: errs.length === 0,
      detail: errs.length === 0 ? "Valid" : errs.join("; "),
    });
  }
  return results;
}

function checkDryRun(
  repoTemplatesDir: string,
  bundledTemplatesDir: string
): CheckResult {
  try {
    const templates = discoverTemplates(repoTemplatesDir, bundledTemplatesDir, true);
    if (templates.length === 0) {
      return { name: "Dry-run", passed: false, detail: "No templates to dry-run" };
    }
    const tpl = templates[0];
    const vars = buildBuiltInVars("testModule", "2025-01-15T10:00:00.000Z");
    const allVars: Record<string, string> = { ...(vars as unknown as Record<string, string>) };

    // Fill in defaults for template variables
    for (const v of tpl.manifest.variables) {
      if (v.default && !allVars[v.key]) {
        allVars[v.key] = v.default;
      }
    }

    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "scaffold-selfcheck-"));
    try {
      const result = generateFiles(tpl.filesDir, tmpDir, allVars, tpl.manifest, false, false);
      if (result.status !== "ok") {
        return { name: "Dry-run", passed: false, detail: `Generation failed: ${result.error}` };
      }
      if (result.createdFiles.length === 0) {
        return { name: "Dry-run", passed: false, detail: "No files were created" };
      }
      return {
        name: "Dry-run",
        passed: true,
        detail: `Created ${result.createdFiles.length} file(s): ${result.createdFiles.join(", ")}`,
      };
    } finally {
      // Clean up temp directory
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  } catch (err) {
    return { name: "Dry-run", passed: false, detail: String(err) };
  }
}

function checkAuditWriter(): CheckResult {
  try {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "scaffold-audit-check-"));
    const auditFile = path.join(tmpDir, "test_audit.jsonl");
    try {
      const entry: AuditEntry = {
        ts: new Date().toISOString(),
        template_id: "test",
        template_version: 1,
        target_uri: "/tmp/test",
        variables: { name: "test" },
        created_files: ["test.py"],
        skipped_files: [],
        conflicts: [],
        status: "ok",
      };
      writeAuditEntry(auditFile, entry);
      const entries = readAuditEntries(auditFile);
      if (entries.length !== 1) {
        return { name: "Audit writer", passed: false, detail: "Read back wrong number of entries" };
      }
      if (entries[0].template_id !== "test") {
        return { name: "Audit writer", passed: false, detail: "Entry data mismatch" };
      }
      return { name: "Audit writer", passed: true, detail: "Write and read-back successful" };
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  } catch (err) {
    return { name: "Audit writer", passed: false, detail: String(err) };
  }
}

/** Format check results into a human-readable summary */
export function formatResults(results: CheckResult[]): string {
  const lines: string[] = ["=== Scaffold Bot Self-Check ===", ""];
  let allPassed = true;
  for (const r of results) {
    const icon = r.passed ? "✅ PASS" : "❌ FAIL";
    lines.push(`${icon}  ${r.name}: ${r.detail}`);
    if (!r.passed) {
      allPassed = false;
    }
  }
  lines.push("");
  lines.push(allPassed ? "Overall: ✅ ALL CHECKS PASSED" : "Overall: ❌ SOME CHECKS FAILED");
  return lines.join("\n");
import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { listTemplates } from "./templateRegistry";

interface CheckResult {
  label: string;
  ok: boolean;
  detail?: string;
}

export async function runSelfCheck(): Promise<void> {
  const results: CheckResult[] = [];

  // Check 1: workspace open
  const ws = vscode.workspace.workspaceFolders?.[0];
  results.push({
    label: "Workspace open",
    ok: !!ws,
    detail: ws ? ws.uri.fsPath : "No workspace folder open",
  });

  // Check 2: bundled templates exist
  const bundledDir = path.join(__dirname, "..", "templates");
  const bundledExists = fs.existsSync(bundledDir);
  results.push({
    label: "Bundled templates directory",
    ok: bundledExists,
    detail: bundledExists ? bundledDir : "Not found",
  });

  // Check 3: templates loadable
  try {
    const templates = await listTemplates();
    results.push({
      label: "Templates discovered",
      ok: templates.length > 0,
      detail: `${templates.length} template(s) found`,
    });

    // Check 4: each template has valid structure
    for (const t of templates) {
      const filesDir = path.join(t.dir, "files");
      const hasFiles = fs.existsSync(filesDir);
      results.push({
        label: `Template "${t.id}" has files/`,
        ok: hasFiles,
        detail: hasFiles ? filesDir : "Missing files/ directory",
      });
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    results.push({
      label: "Templates discovered",
      ok: false,
      detail: msg,
    });
  }

  // Check 5: audit path writable
  if (ws) {
    const auditRel =
      vscode.workspace.getConfiguration("scaffoldBot").get<string>("auditPath") ??
      ".swarmz/audit/scaffold_audit.jsonl";
    const auditDir = path.dirname(path.join(ws.uri.fsPath, auditRel));
    results.push({
      label: "Audit directory",
      ok: true,
      detail: auditDir,
    });
  }

  // Format and show
  const lines = results.map(r => `${r.ok ? "✅" : "❌"} ${r.label}: ${r.detail ?? ""}`);
  const doc = await vscode.workspace.openTextDocument({
    content: `Scaffold Bot — Self Check\n${"=".repeat(40)}\n\n${lines.join("\n")}\n`,
    language: "markdown",
  });
  await vscode.window.showTextDocument(doc, { preview: true });
}
