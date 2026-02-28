# Helper1 Validation Engine v0.2.0

## Scope
This document defines the canonical helper1 v0.2.0 command interface used by `/v1/agents/helper1/run`.

## Request Contract
Route: `POST /v1/agents/helper1/run`

Fields:
- `query` (string, optional): legacy input for compatibility mode.
- `command` (string, optional, default `echo`): one of `echo`, `validate_manifest`, `validate_proposal`.
- `payload` (object, optional): command payload.

Compatibility behavior:
- If request uses only `query`, server executes `echo` and sets `compatibility_mode.legacy_query=true`.
- If `command` is provided, server dispatches command engine and applies command-based capability grant checks.

## Command Payloads
`echo`
- Payload: any object.
- Result: `{ "echo": <payload>, "source": "helper1" }`.

`validate_manifest`
- Payload:
  - `manifest` (object): manifest candidate.
- Result fields:
  - `valid` (bool)
  - `risk_score` (0.0-1.0)
  - `errors` (array)
  - `warnings` (array)
  - `suggestions` (array)
  - `summary` (string)

`validate_proposal`
- Payload:
  - `manifest` (object, optional)
  - `code_snippet` (string, optional)
- Result fields:
  - all report fields above
  - `approved_for_ritual` (bool), true when risk score is `< 0.3` and no errors.

## Invariant Semantics
Helper1 reports additional risk/warnings for:
- non-additive mutation intent markers
- core-boundary mutation markers
- death-state safety markers
- extension consistency checks for `pantheon`, `quantum`, `cosmic`

## Code Safety Heuristics
`validate_proposal` performs static checks on `code_snippet`:
- Parses Python via `ast.parse`.
- Flags high-risk tokens/imports: `os`, `subprocess`, `eval`, `exec`, `__import__`.

## Risk Interpretation
- `0.0` to `<0.3`: low risk, potentially ritual-approvable.
- `0.3` to `<0.7`: medium risk, operator review expected.
- `>=0.7`: high risk, deny-by-default unless explicitly approved.

## Example Requests
Legacy compatibility:
```json
{
  "query": "hello"
}
```

Manifest validation:
```json
{
  "command": "validate_manifest",
  "payload": {
    "manifest": {
      "id": "helper1@0.2.0",
      "version": "0.2.0",
      "capabilities": ["data.read", "agent.introspect"]
    }
  }
}
```

Proposal validation:
```json
{
  "command": "validate_proposal",
  "payload": {
    "manifest": {"id": "candidate@1.0.0"},
    "code_snippet": "def x():\n    return 1"
  }
}
```
