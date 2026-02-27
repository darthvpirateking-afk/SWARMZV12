import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { AuditEntry, readAuditEntries, writeAuditEntry } from "./audit";
import { generateFiles } from "./fsOps";
import { buildBuiltInVars, renderString, toKebabCase, toPascalCase, toSnakeCase } from "./render";
import { discoverTemplates, validateManifest } from "./templateRegistry";

export interface CheckResult {
  detail: string;
  name: string;
  passed: boolean;
}

function checkTransforms(): CheckResult {
  const checks = [
    { fn: toSnakeCase, input: "myModuleName", expected: "my_module_name" },
    { fn: toKebabCase, input: "myModuleName", expected: "my-module-name" },
    { fn: toPascalCase, input: "my-module-name", expected: "MyModuleName" },
  ];
  for (const check of checks) {
    const result = check.fn(check.input);
    if (result !== check.expected) {
      return {
        detail: `${check.fn.name}(${check.input}) -> ${result}, expected ${check.expected}`,
        name: "Transforms",
        passed: false,
      };
    }
  }
  return { detail: "All transform checks passed", name: "Transforms", passed: true };
}

function checkPlaceholderRendering(): CheckResult {
  const vars = buildBuiltInVars("userAuth", "2025-01-15T10:00:00.000Z");
  const rendered = renderString(
    "{{name}}/{{snakeName}}/{{year}}",
    vars as unknown as Record<string, string>
  );
  if (rendered !== "userAuth/user_auth/2025") {
    return {
      detail: `placeholder output mismatch: ${rendered}`,
      name: "Placeholder rendering",
      passed: false,
    };
  }
  return { detail: "Placeholder rendering works", name: "Placeholder rendering", passed: true };
}

function checkManifests(repoTemplatesDir: string, bundledTemplatesDir: string): CheckResult[] {
  const templates = discoverTemplates(repoTemplatesDir, bundledTemplatesDir, true);
  if (templates.length === 0) {
    return [{ detail: "No templates discovered", name: "Manifest discovery", passed: false }];
  }
  return templates.map((template) => {
    const errors = validateManifest(template.manifest);
    return {
      detail: errors.length === 0 ? "Valid" : errors.join("; "),
      name: `Manifest: ${template.manifest.id}`,
      passed: errors.length === 0,
    };
  });
}

function checkDryRun(repoTemplatesDir: string, bundledTemplatesDir: string): CheckResult {
  const templates = discoverTemplates(repoTemplatesDir, bundledTemplatesDir, true);
  if (templates.length === 0) {
    return { detail: "No templates available", name: "Dry-run", passed: false };
  }
  const template = templates[0];
  const vars = buildBuiltInVars("sampleModule", "2025-01-15T10:00:00.000Z");
  for (const variable of template.manifest.variables) {
    if (variable.default && !vars[variable.key as keyof typeof vars]) {
      (vars as unknown as Record<string, string>)[variable.key] = variable.default;
    }
  }
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "scaffold-bot-selfcheck-"));
  try {
    const result = generateFiles(
      template.filesDir,
      tempDir,
      vars as unknown as Record<string, string>,
      template.manifest,
      false,
      true
    );
    return {
      detail: result.status === "ok" ? "Dry-run succeeded" : `Dry-run failed: ${result.error}`,
      name: "Dry-run",
      passed: result.status === "ok",
    };
  } finally {
    fs.rmSync(tempDir, { force: true, recursive: true });
  }
}

function checkAuditWriter(): CheckResult {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "scaffold-bot-audit-"));
  const auditPath = path.join(tempDir, "audit.jsonl");
  const entry: AuditEntry = {
    conflicts: [],
    created_files: ["a.txt"],
    skipped_files: [],
    status: "ok",
    target_uri: "C:/tmp",
    template_id: "self-check",
    template_version: 1,
    ts: new Date().toISOString(),
    variables: { name: "test" },
  };
  try {
    writeAuditEntry(auditPath, entry);
    const entries = readAuditEntries(auditPath);
    return {
      detail: entries.length === 1 ? "Audit append/read successful" : "Audit read count mismatch",
      name: "Audit writer",
      passed: entries.length === 1,
    };
  } finally {
    fs.rmSync(tempDir, { force: true, recursive: true });
  }
}

export function runSelfChecks(repoTemplatesDir: string, bundledTemplatesDir: string): CheckResult[] {
  return [
    checkTransforms(),
    checkPlaceholderRendering(),
    ...checkManifests(repoTemplatesDir, bundledTemplatesDir),
    checkDryRun(repoTemplatesDir, bundledTemplatesDir),
    checkAuditWriter(),
  ];
}

export function formatResults(results: CheckResult[]): string {
  const lines: string[] = ["=== Scaffold Bot Self-Check ===", ""];
  for (const result of results) {
    lines.push(`${result.passed ? "PASS" : "FAIL"} ${result.name}: ${result.detail}`);
  }
  lines.push("");
  lines.push(results.every((item) => item.passed) ? "Overall: PASS" : "Overall: FAIL");
  return lines.join("\n");
}
