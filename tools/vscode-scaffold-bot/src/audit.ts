/**
 * Append-only JSONL audit log writer.
 */

import * as path from "path";
import * as fs from "fs";

export interface AuditEntry {
  ts: string;
  template_id: string;
  template_version: number;
  target_uri: string;
  variables: Record<string, string>;
  created_files: string[];
  skipped_files: string[];
  conflicts: string[];
  status: "ok" | "fail";
  error?: string;
}

/**
 * Append an audit entry to the JSONL log file.
 * Creates parent directories and the file if they don't exist.
 *
 * @param auditFilePath Absolute path to the audit JSONL file
 * @param entry The audit entry to write
 */
export function writeAuditEntry(auditFilePath: string, entry: AuditEntry): void {
  const dir = path.dirname(auditFilePath);
  fs.mkdirSync(dir, { recursive: true });
  const line = JSON.stringify(entry) + "\n";
  fs.appendFileSync(auditFilePath, line, "utf-8");
}

/**
 * Read all audit entries from the log file.
 * Returns an empty array if the file doesn't exist.
 */
export function readAuditEntries(auditFilePath: string): AuditEntry[] {
  if (!fs.existsSync(auditFilePath)) {
    return [];
  }
  const content = fs.readFileSync(auditFilePath, "utf-8");
  return content
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as AuditEntry);
import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

export interface AuditEntry {
  timestamp: string;
  templateId: string;
  templateVersion: string;
  targetDir: string;
  filesWritten: string[];
  filesSkipped: string[];
  variables: Record<string, string>;
}

function getAuditPath(): string | null {
  const ws = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (!ws) return null;
  const rel =
    vscode.workspace.getConfiguration("scaffoldBot").get<string>("auditPath") ??
    ".swarmz/audit/scaffold_audit.jsonl";
  return path.join(ws.fsPath, rel);
}

export async function appendAudit(entry: AuditEntry): Promise<void> {
  const auditPath = getAuditPath();
  if (!auditPath) return;

  const dir = path.dirname(auditPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const line = JSON.stringify(entry) + "\n";
  fs.appendFileSync(auditPath, line, "utf-8");
}
