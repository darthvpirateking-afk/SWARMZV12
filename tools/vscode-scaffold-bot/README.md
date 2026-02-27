# Scaffold Bot (SWARMZ)

Local-first VS Code extension for deterministic template scaffolding with audit logging.

## Commands

- `scaffoldBot.scaffoldHere`: Scaffold into a selected folder from Explorer.
- `scaffoldBot.scaffold`: Choose a folder and scaffold from command palette.
- `scaffoldBot.manageTemplates`: Reveal template directory.
- `scaffoldBot.selfCheck`: Run local self-check report.

## Template Format

Each template folder contains:

```text
<template-id>/
  template.json
  files/
    ...
```

`template.json` schema:

```json
{
  "id": "module_fastapi_router",
  "title": "FastAPI Router Module",
  "description": "Generates a FastAPI router module with __init__.py, router file, and test file.",
  "version": 1,
  "variables": [
    {
      "key": "name",
      "prompt": "Module name",
      "default": "myModule"
    }
  ],
  "output": {
    "root": ".",
    "path": "{{kebabName}}",
    "conflict": "fail"
  }
}
```
