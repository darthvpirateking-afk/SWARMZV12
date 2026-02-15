import * as vscode from "vscode";
import { listTemplates, loadTemplate, TemplateMeta } from "./templateRegistry";
import { buildCtx, RenderCtx } from "./render";
import { planFromTemplate, generateFromTemplate } from "./fsOps";
import { appendAudit, AuditEntry } from "./audit";
import { runSelfCheck } from "./selfCheck";

const wsRoot = () => {
  const w = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (!w) throw new Error("Open a workspace folder first.");
  return w;
};

async function pickFolder(): Promise<vscode.Uri | null> {
  const p = await vscode.window.showOpenDialog({
    canSelectFolders: true,
    canSelectFiles: false,
    canSelectMany: false,
  });
  return p?.[0] ?? null;
}

async function pickTemplate(): Promise<TemplateMeta | null> {
  const ts = await listTemplates();
  if (!ts.length) throw new Error("No templates found.");
  const pick = await vscode.window.showQuickPick(
    ts.map(t => ({
      label: t.title,
      description: `${t.id} • v${t.version} • ${t.source}`,
      detail: t.description,
      t,
    })),
    { placeHolder: "Select a scaffold template" }
  );
  return pick?.t ?? null;
}

async function promptVars(
  t: TemplateMeta
): Promise<Record<string, string> | null> {
  const vars: Record<string, string> = {};
  for (const v of t.variables) {
    const value = await vscode.window.showInputBox({
      prompt: v.prompt,
      value: v.default ?? "",
      placeHolder: v.name,
    });
    if (value === undefined) return null; // cancelled
    vars[v.name] = value;
  }
  return vars;
}

async function doScaffold(targetUri: vscode.Uri): Promise<void> {
  const tpl = await pickTemplate();
  if (!tpl) return;

  const vars = await promptVars(tpl);
  if (!vars) return;

  const ctx: RenderCtx = buildCtx(vars);
  const plans = planFromTemplate(tpl, targetUri.fsPath, ctx);

  if (!plans.length) {
    vscode.window.showWarningMessage("Template produced no files.");
    return;
  }

  const cfg = vscode.workspace.getConfiguration("scaffoldBot");
  const confirmBeforeWrite = cfg.get<boolean>("confirmBeforeWrite") ?? true;
  const allowOverwrite = cfg.get<boolean>("allowOverwrite") ?? false;

  if (confirmBeforeWrite) {
    const fileList = plans.map(p => p.relativePath).join(", ");
    const answer = await vscode.window.showInformationMessage(
      `Scaffold will create ${plans.length} file(s): ${fileList}`,
      { modal: true },
      "Create"
    );
    if (answer !== "Create") return;
  }

  const { written, skipped } = await generateFromTemplate(plans, allowOverwrite);

  const entry: AuditEntry = {
    timestamp: new Date().toISOString(),
    templateId: tpl.id,
    templateVersion: tpl.version,
    targetDir: targetUri.fsPath,
    filesWritten: written,
    filesSkipped: skipped,
    variables: vars,
  };
  await appendAudit(entry);

  const msg = [`✅ ${written.length} file(s) created.`];
  if (skipped.length) msg.push(`⚠️ ${skipped.length} skipped (already exist).`);
  vscode.window.showInformationMessage(msg.join(" "));
}

async function manageTemplates(): Promise<void> {
  const ts = await listTemplates();
  const items = ts.map(t => ({
    label: t.title,
    description: `${t.id} • v${t.version} • ${t.source}`,
    detail: `${t.dir}`,
  }));

  if (!items.length) {
    vscode.window.showInformationMessage(
      "No templates found. Add templates to .swarmz/templates/ or use the bundled ones."
    );
    return;
  }

  const pick = await vscode.window.showQuickPick(items, {
    placeHolder: "Installed templates (select to reveal in explorer)",
  });

  if (pick) {
    const uri = vscode.Uri.file(pick.detail);
    await vscode.commands.executeCommand("revealFileInOS", uri);
  }
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.scaffoldHere", async (uri?: vscode.Uri) => {
      try {
        const target = uri ?? wsRoot();
        await doScaffold(target);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        vscode.window.showErrorMessage(`Scaffold Bot: ${msg}`);
      }
    }),

    vscode.commands.registerCommand("scaffoldBot.scaffold", async () => {
      try {
        const folder = await pickFolder();
        if (!folder) return;
        await doScaffold(folder);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        vscode.window.showErrorMessage(`Scaffold Bot: ${msg}`);
      }
    }),

    vscode.commands.registerCommand("scaffoldBot.manageTemplates", async () => {
      try {
        await manageTemplates();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        vscode.window.showErrorMessage(`Scaffold Bot: ${msg}`);
      }
    }),

    vscode.commands.registerCommand("scaffoldBot.selfCheck", async () => {
      try {
        await runSelfCheck();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        vscode.window.showErrorMessage(`Scaffold Bot: ${msg}`);
      }
    })
  );
}

export function deactivate(): void {}
