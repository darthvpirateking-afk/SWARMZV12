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
