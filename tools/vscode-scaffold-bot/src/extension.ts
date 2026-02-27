import * as path from "path";
import * as vscode from "vscode";
import { AuditEntry, writeAuditEntry } from "./audit";
import { generateFiles } from "./fsOps";
import { applyTransform, buildBuiltInVars } from "./render";
import { formatResults, runSelfChecks } from "./selfCheck";
import { discoverTemplates, TemplateEntry, VariableDef } from "./templateRegistry";

function getConfig() {
  const cfg = vscode.workspace.getConfiguration("scaffoldBot");
  return {
    allowOverwrite: cfg.get<boolean>("allowOverwrite", false),
    auditPath: cfg.get<string>("auditPath", ".swarmz/audit/scaffold_audit.jsonl"),
    confirmBeforeWrite: cfg.get<boolean>("confirmBeforeWrite", true),
    preferRepoTemplates: cfg.get<boolean>("preferRepoTemplates", true),
    templatesPath: cfg.get<string>("templatesPath", ".swarmz/templates"),
  };
}

function getWorkspaceRoot(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function getBundledTemplatesDir(context: vscode.ExtensionContext): string {
  return path.join(context.extensionPath, "templates");
}

function getRepoTemplatesDir(): string | undefined {
  const root = getWorkspaceRoot();
  if (!root) {
    return undefined;
  }
  return path.join(root, getConfig().templatesPath);
}

function getAuditFilePath(): string | undefined {
  const root = getWorkspaceRoot();
  if (!root) {
    return undefined;
  }
  return path.join(root, getConfig().auditPath);
}

async function pickTemplate(context: vscode.ExtensionContext): Promise<TemplateEntry | undefined> {
  const repoDir = getRepoTemplatesDir() || "";
  const bundledDir = getBundledTemplatesDir(context);
  const templates = discoverTemplates(repoDir, bundledDir, getConfig().preferRepoTemplates);

  if (templates.length === 0) {
    vscode.window.showErrorMessage("Scaffold Bot: No templates found.");
    return undefined;
  }

  const picked = await vscode.window.showQuickPick(
    templates.map((template) => ({
      description: `(${template.source}) v${template.manifest.version}`,
      detail: template.manifest.description,
      entry: template,
      label: template.manifest.title,
    })),
    { placeHolder: "Select a template" }
  );
  return picked?.entry;
}

async function promptVariables(
  variables: VariableDef[]
): Promise<Record<string, string> | undefined> {
  const values: Record<string, string> = {};
  for (const variable of variables) {
    const value = await vscode.window.showInputBox({
      prompt: variable.prompt,
      value: variable.default || "",
      validateInput: (input) => {
        if (!input || input.trim().length === 0) {
          return "Value is required";
        }
        if (variable.pattern) {
          const regex = new RegExp(variable.pattern);
          if (!regex.test(input)) {
            return `Must match pattern: ${variable.pattern}`;
          }
        }
        return undefined;
      },
    });
    if (value === undefined) {
      return undefined;
    }
    values[variable.key] = variable.transform ? applyTransform(value, variable.transform) : value;
  }
  return values;
}

async function runScaffold(
  context: vscode.ExtensionContext,
  targetFolderUri?: vscode.Uri
): Promise<void> {
  const template = await pickTemplate(context);
  if (!template) {
    return;
  }

  const targetDir =
    targetFolderUri?.fsPath ||
    (
      await vscode.window.showOpenDialog({
        canSelectFiles: false,
        canSelectFolders: true,
        canSelectMany: false,
        openLabel: "Select target folder",
      })
    )?.[0]?.fsPath;
  if (!targetDir) {
    return;
  }

  const userVars = await promptVariables(template.manifest.variables);
  if (!userVars) {
    return;
  }

  const primaryKey = template.manifest.variables[0]?.key || "name";
  const rawName = userVars.name || userVars[primaryKey] || "module";
  const builtInVars = buildBuiltInVars(rawName);
  const allVars: Record<string, string> = {
    ...(builtInVars as unknown as Record<string, string>),
    ...userVars,
  };

  if (getConfig().confirmBeforeWrite) {
    const preview = `Template: ${template.manifest.title}\nTarget: ${targetDir}\nVariables: ${JSON.stringify(
      userVars,
      null,
      2
    )}`;
    const choice = await vscode.window.showInformationMessage(preview, { modal: true }, "Generate");
    if (choice !== "Generate") {
      return;
    }
  }

  const result = generateFiles(
    template.filesDir,
    targetDir,
    allVars,
    template.manifest,
    getConfig().allowOverwrite
  );

  const auditPath = getAuditFilePath();
  if (auditPath) {
    const entry: AuditEntry = {
      conflicts: result.conflicts,
      created_files: result.createdFiles,
      error: result.error,
      skipped_files: result.skippedFiles,
      status: result.status,
      target_uri: targetDir,
      template_id: template.manifest.id,
      template_version: template.manifest.version,
      ts: new Date().toISOString(),
      variables: allVars,
    };
    writeAuditEntry(auditPath, entry);
  }

  if (result.status === "ok") {
    vscode.window.showInformationMessage(
      `Scaffold Bot: Created ${result.createdFiles.length} file(s), skipped ${result.skippedFiles.length}.`
    );
  } else {
    vscode.window.showErrorMessage(`Scaffold Bot: ${result.error}`);
  }
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.scaffoldHere", (uri?: vscode.Uri) =>
      runScaffold(context, uri)
    )
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.scaffold", () => runScaffold(context))
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.manageTemplates", async () => {
      const repoDir = getRepoTemplatesDir();
      const fallbackDir = getBundledTemplatesDir(context);
      const uri = vscode.Uri.file(repoDir || fallbackDir);
      await vscode.commands.executeCommand("revealInExplorer", uri);
    })
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.selfCheck", async () => {
      const repoDir = getRepoTemplatesDir() || "";
      const bundledDir = getBundledTemplatesDir(context);
      const summary = formatResults(runSelfChecks(repoDir, bundledDir));
      const doc = await vscode.workspace.openTextDocument({
        content: summary,
        language: "plaintext",
      });
      await vscode.window.showTextDocument(doc, { preview: true });
    })
  );
}

export function deactivate(): void {
  // No-op.
}
