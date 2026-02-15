# Scaffold Bot (SWARMZ)

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
| `scaffoldBot.templatesPath` | string | `.swarmz/templates` | Path to repo-local templates |
| `scaffoldBot.auditPath` | string | `.swarmz/audit/scaffold_audit.jsonl` | Audit log file path |
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

## Bundled Templates

- **module_fastapi_router** — FastAPI router module with init, router, and test files
