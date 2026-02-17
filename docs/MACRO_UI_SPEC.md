# MACRO UI SPEC — REQUIREMENTS

## GOAL
Provide a simple UI panel that lets the operator:
1. See the top repeated sequence of the day.
2. Generate a macro from that sequence.
3. View existing macros.
4. Trigger macro execution (PREPARE ONLY, no REALITY actions).
5. Inspect macro details.

This UI must NOT change any backend behavior.
It is purely a front-end panel that calls existing scripts.

---

## UI SECTIONS

### SECTION 1 — DAILY SUMMARY PANEL
- Title: “Daily Workflow Summary”
- Shows:
  * Top repeated sequence ID
  * Number of occurrences
  * Estimated value score (from value_report)
- Buttons:
  * “Generate Macro from Top Sequence”
      → Runs: python tools/build_macro.py --sequence <top_id>
  * “Refresh Summary”
      → Re-runs: normalize_events, mine_sequences, value_report

### SECTION 2 — MACRO LIST PANEL
- Title: “Your Macros”
- Shows a scrollable list of macros stored in:
    data/macros/*.json
- For each macro:
  * macro_id
  * title
  * created_at
  * number of steps
- Buttons per macro:
  * “View”
  * “Prepare Run”
      → PREPARE ONLY: does not execute REALITY actions
  * “Export” (optional, add-only)

### SECTION 3 — MACRO DETAIL VIEW
- Shows:
  * macro_id
  * title
  * created_at
  * steps (list)
  * artifacts (if any)
  * confidence score
  * depends_on list
- Buttons:
  * “Prepare Run”
  * “Back to List”

---

## BACKEND HOOKS (ADD-ONLY)
The UI must call existing scripts only.
No new backend logic.
No modifications to existing modules.

Allowed calls:
- python tools/build_macro.py --sequence <id>
- python tools/normalize_events.py
- python tools/mine_sequences.py
- python tools/value_report.py

Optional:
- python tools/prepare_macro_run.py (if exists)
- python tools/export_macro.py (if exists)

---

## FAIL-OPEN REQUIREMENTS
If any script fails:
- UI must show a non-blocking warning.
- UI must not crash.
- UI must not stop operator workflow.