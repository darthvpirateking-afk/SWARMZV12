import * as fs from "fs";
import * as path from "path";

export interface AuditEntry {
  conflicts: string[];
  created_files: string[];
  error?: string;
  skipped_files: string[];
  status: "ok" | "fail";
  target_uri: string;
  template_id: string;
  template_version: number;
  ts: string;
  variables: Record<string, string>;
}

export function writeAuditEntry(auditFilePath: string, entry: AuditEntry): void {
  fs.mkdirSync(path.dirname(auditFilePath), { recursive: true });
  fs.appendFileSync(auditFilePath, `${JSON.stringify(entry)}\n`, "utf-8");
}

export function readAuditEntries(auditFilePath: string): AuditEntry[] {
  if (!fs.existsSync(auditFilePath)) {
    return [];
  }
  return fs
    .readFileSync(auditFilePath, "utf-8")
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as AuditEntry);
}
