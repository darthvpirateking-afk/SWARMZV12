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
