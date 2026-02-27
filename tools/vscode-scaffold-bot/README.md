# Scaffold Bot — VS Code Extension

A local-first, template-driven VS Code extension that scaffolds folders and files from templates with placeholder substitution.

## Features

- **Template-driven scaffolding** — generate file trees from JSON-defined templates
- **Placeholder substitution** — in both filenames and file contents
- **Deterministic transforms** — snake_case, kebab-case, PascalCase, lower, upper
- **Conflict handling** — fail, skip, or merge strategies
- **Audit logging** — append-only JSONL log of every scaffold operation
- **Self-check** — built-in validation of transforms, manifests, rendering, and audit

## Commands

| Command                         | Description                        |
| ------------------------------- | ---------------------------------- |
| `Scaffold: New Module Here`     | Scaffold into the right-clicked folder |
| `Scaffold: New Module`          | Pick a target folder, then scaffold    |
| `Scaffold: Manage Templates`    | Open the templates directory           |
| `Scaffold: Self-Check`          | Run deterministic validation checks    |

## Settings

| Setting                            | Default                                  | Description                              |
| ---------------------------------- | ---------------------------------------- | ---------------------------------------- |
| `scaffoldBot.templatesPath`        | `.nexusmon/templates`                      | Repo-level templates directory           |
| `scaffoldBot.auditPath`            | `.nexusmon/audit/scaffold_audit.jsonl`     | Audit log file path                      |
| `scaffoldBot.confirmBeforeWrite`   | `true`                                   | Show preview before generating           |
| `scaffoldBot.allowOverwrite`       | `false`                                  | Allow overwriting in merge mode          |
| `scaffoldBot.preferRepoTemplates`  | `true`                                   | Prefer repo templates over bundled ones  |

## Template Format

Each template lives in its own folder containing:

```
my-template/
  template.json
  files/
    ... (file tree with {{placeholder}} tokens)
# Scaffold Bot (NEXUSMON)

A local-first VS Code extension for template scaffolding with placeholder substitution and audit logging.

## Features

- **Template scaffolding** — Generate files from templates with variable substitution
- **Explorer integration** — Right-click a folder to scaffold a new module
- **Audit trail** — Every scaffold operation is logged to a JSONL audit file
- **Self-check** — Validate that templates and configuration are healthy
- **Repo-local templates** — Override bundled templates with project-specific ones

## Commands

| Command | Title |
|---------|-------|
| `scaffoldBot.scaffoldHere` | Scaffold: New Module Here |
| `scaffoldBot.scaffold` | Scaffold: New Module (Choose Folder) |
| `scaffoldBot.manageTemplates` | Scaffold: Manage Templates |
| `scaffoldBot.selfCheck` | Scaffold: Self Check |

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `scaffoldBot.templatesPath` | string | `.nexusmon/templates` | Path to repo-local templates |
| `scaffoldBot.auditPath` | string | `.nexusmon/audit/scaffold_audit.jsonl` | Audit log file path |
| `scaffoldBot.confirmBeforeWrite` | boolean | `true` | Confirm before writing files |
| `scaffoldBot.allowOverwrite` | boolean | `false` | Allow overwriting existing files |
| `scaffoldBot.preferRepoTemplates` | boolean | `true` | Prefer repo templates over bundled |

## Template Format

Templates live in directories with a `template.json` manifest:

```
templates/
  my_template/
    template.json
    files/
      {{snakeName}}.py
      test_{{snakeName}}.py
```

### template.json

```json
{
  "id": "my_template",
  "title": "My Template",
  "description": "Description of the template",
  "version": 1,
  "variables": [
    {
      "key": "name",
      "prompt": "Module name",
      "default": "myModule",
      "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$",
      "transform": "lower"
    }
  ],
  "output": {
    "root": ".",
    "path": "{{kebabName}}",
    "conflict": "fail"
  }
}
```

### Available Placeholders

| Placeholder        | Example Input  | Output            |
| ------------------ | -------------- | ----------------- |
| `{{name}}`         | `userAuth`     | `userAuth`        |
| `{{snakeName}}`    | `userAuth`     | `user_auth`       |
| `{{kebabName}}`    | `userAuth`     | `user-auth`       |
| `{{pascalName}}`   | `userAuth`     | `UserAuth`        |
| `{{timestampISO}}` | —              | ISO 8601 string   |
| `{{year}}`         | —              | `2025`            |

## Template Locations

1. **Repo-level** (preferred): `.nexusmon/templates/` in your workspace root
2. **Bundled fallback**: `tools/vscode-scaffold-bot/templates/` in the extension
  "description": "Description of what this template creates.",
  "version": "1.0.0",
  "variables": [
    { "name": "name", "prompt": "Module name", "default": "example" }
  ]
}
```

### Placeholder Variables

When a `name` variable is provided, the following derived variables are automatically available:

| Variable | Example (input: `userProfile`) |
|----------|-------------------------------|
| `{{name}}` | `userProfile` |
| `{{snakeName}}` | `user_profile` |
| `{{camelName}}` | `userProfile` |
| `{{PascalName}}` | `UserProfile` |
| `{{kebabName}}` | `user-profile` |

## Development

```bash
cd tools/vscode-scaffold-bot
npm install
npm run compile
```

Then press F5 in VS Code to launch the Extension Development Host.

## Built-in Template

**FastAPI Router Module** (`module_fastapi_router`) generates:
- `__init__.py`
- `{snake_name}.py` — FastAPI router with CRUD endpoints
- `test_{snake_name}.py` — test stubs
## Bundled Templates

- **module_fastapi_router** — FastAPI router module with init, router, and test files

