/**
 * VS Code Scaffold Bot — main entry point.
 * Registers commands and wires together template discovery, rendering, and audit.
 */

import * as vscode from "vscode";
import * as path from "path";
import { discoverTemplates, TemplateEntry, VariableDef } from "./templateRegistry";
import { buildBuiltInVars, renderString, applyTransform } from "./render";
import { generateFiles } from "./fsOps";
import { writeAuditEntry, AuditEntry } from "./audit";
import { runSelfChecks, formatResults } from "./selfCheck";

function getConfig() {
  const cfg = vscode.workspace.getConfiguration("scaffoldBot");
  return {
    templatesPath: cfg.get<string>("templatesPath", ".swarmz/templates"),
    auditPath: cfg.get<string>("auditPath", ".swarmz/audit/scaffold_audit.jsonl"),
    confirmBeforeWrite: cfg.get<boolean>("confirmBeforeWrite", true),
    allowOverwrite: cfg.get<boolean>("allowOverwrite", false),
    preferRepoTemplates: cfg.get<boolean>("preferRepoTemplates", true),
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
  const cfg = getConfig();
  return path.join(root, cfg.templatesPath);
}

function getAuditFilePath(): string | undefined {
  const root = getWorkspaceRoot();
  if (!root) {
    return undefined;
  }
  const cfg = getConfig();
  return path.join(root, cfg.auditPath);
}

async function pickTemplate(
  context: vscode.ExtensionContext
): Promise<TemplateEntry | undefined> {
  const cfg = getConfig();
  const repoDir = getRepoTemplatesDir() || "";
  const bundledDir = getBundledTemplatesDir(context);
  const templates = discoverTemplates(repoDir, bundledDir, cfg.preferRepoTemplates);

  if (templates.length === 0) {
    vscode.window.showErrorMessage("Scaffold Bot: No templates found.");
    return undefined;
  }

  const items = templates.map((t) => ({
    label: t.manifest.title,
    description: `(${t.source}) v${t.manifest.version}`,
    detail: t.manifest.description,
    entry: t,
  }));

  const picked = await vscode.window.showQuickPick(items, {
    placeHolder: "Select a template",
  });

  return picked?.entry;
}

async function promptVariables(
  variables: VariableDef[]
): Promise<Record<string, string> | undefined> {
  const result: Record<string, string> = {};
  for (const v of variables) {
    const value = await vscode.window.showInputBox({
      prompt: v.prompt,
      value: v.default || "",
      validateInput: (input) => {
        if (v.pattern) {
          const regex = new RegExp(v.pattern);
          if (!regex.test(input)) {
            return `Must match pattern: ${v.pattern}`;
          }
        }
        if (!input || input.trim().length === 0) {
          return "Value is required";
        }
        return undefined;
      },
    });
    if (value === undefined) {
      return undefined; // User cancelled
    }
    let finalValue = value;
    if (v.transform) {
      finalValue = applyTransform(value, v.transform);
    }
    result[v.key] = finalValue;
  }
  return result;
}

async function runScaffold(
  context: vscode.ExtensionContext,
  targetFolderUri?: vscode.Uri
): Promise<void> {
  // 1. Pick template
  const template = await pickTemplate(context);
  if (!template) {
    return;
  }

  // 2. Determine target folder
  let targetDir: string;
  if (targetFolderUri) {
    targetDir = targetFolderUri.fsPath;
  } else {
    const folders = await vscode.window.showOpenDialog({
      canSelectFolders: true,
      canSelectFiles: false,
      canSelectMany: false,
      openLabel: "Select target folder",
    });
    if (!folders || folders.length === 0) {
      return;
    }
    targetDir = folders[0].fsPath;
  }

  // 3. Prompt variables
  const userVars = await promptVariables(template.manifest.variables);
  if (!userVars) {
    return;
  }

  // 4. Build all vars (name comes from the first variable, typically "name")
  const nameVar = userVars["name"] || userVars[template.manifest.variables[0]?.key] || "module";
  const builtInVars = buildBuiltInVars(nameVar);
  const allVars: Record<string, string> = {
    ...(builtInVars as unknown as Record<string, string>),
    ...userVars,
  };

  // 5. Preview
  const cfg = getConfig();
  if (cfg.confirmBeforeWrite) {
    const outputPath = renderString(template.manifest.output.path, allVars);
    const preview = `Template: ${template.manifest.title}\nTarget: ${path.join(targetDir, outputPath)}\nVariables: ${JSON.stringify(userVars, null, 2)}`;
    const choice = await vscode.window.showInformationMessage(
      preview,
      { modal: true },
      "Generate"
    );
    if (choice !== "Generate") {
      return;
    }
  }

  // 6. Generate
  const result = generateFiles(
    template.filesDir,
    targetDir,
    allVars,
    template.manifest,
    cfg.allowOverwrite
  );

  // 7. Audit
  const auditPath = getAuditFilePath();
  if (auditPath) {
    const entry: AuditEntry = {
      ts: new Date().toISOString(),
      template_id: template.manifest.id,
      template_version: template.manifest.version,
      target_uri: targetDir,
      variables: allVars,
      created_files: result.createdFiles,
      skipped_files: result.skippedFiles,
      conflicts: result.conflicts,
      status: result.status,
      error: result.error,
    };
    try {
      writeAuditEntry(auditPath, entry);
    } catch (err) {
      vscode.window.showWarningMessage(
        `Scaffold Bot: Failed to write audit log: ${err}`
      );
    }
  }

  // 8. Report result
  if (result.status === "ok") {
    vscode.window.showInformationMessage(
      `Scaffold Bot: Created ${result.createdFiles.length} file(s)` +
        (result.skippedFiles.length > 0
          ? `, skipped ${result.skippedFiles.length}`
          : "")
    );
  } else {
    vscode.window.showErrorMessage(
      `Scaffold Bot: Generation failed — ${result.error}`
    );
  }
}

export function activate(context: vscode.ExtensionContext): void {
  // scaffoldBot.scaffoldHere — triggered from explorer context menu
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "scaffoldBot.scaffoldHere",
      (uri?: vscode.Uri) => runScaffold(context, uri)
    )
  );

  // scaffoldBot.scaffold — triggered from command palette
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.scaffold", () =>
      runScaffold(context)
    )
  );

  // scaffoldBot.manageTemplates — open templates location
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.manageTemplates", async () => {
      const repoDir = getRepoTemplatesDir();
      const bundledDir = getBundledTemplatesDir(context);
      const dir = repoDir || bundledDir;
      const uri = vscode.Uri.file(dir);
      await vscode.commands.executeCommand("revealInExplorer", uri);
    })
  );

  // scaffoldBot.selfCheck — deterministic self-check
  context.subscriptions.push(
    vscode.commands.registerCommand("scaffoldBot.selfCheck", async () => {
      const repoDir = getRepoTemplatesDir() || "";
      const bundledDir = getBundledTemplatesDir(context);
      const results = runSelfChecks(repoDir, bundledDir);
      const summary = formatResults(results);

      const doc = await vscode.workspace.openTextDocument({
        content: summary,
        language: "plaintext",
      });
      await vscode.window.showTextDocument(doc);
    })
  );
}

export function deactivate(): void {
  // Nothing to clean up
}
