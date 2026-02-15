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
}
