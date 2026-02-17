# SWARMZ — DAILY OPERATOR RITUAL (MINIMAL + ADD‑ONLY)

## ONE‑TIME SETUP
1. Start SWARMZ normally.
2. Confirm file exists:
   data/activity/events.jsonl
3. Run any mission or command.
4. Confirm events.jsonl grows.
   If not → fix recorder before doing anything else.

---

## DAILY START (RITUAL A — 5 seconds)
Run:
    python tools/verify_activity_stream.py

If entries appear → continue working.
If empty → restart SWARMZ.

---

## DAILY END (RITUAL B — ~60 seconds)
Run in order:
    python tools/normalize_events.py
    python tools/mine_sequences.py
    python tools/value_report.py

Then open:
    data/activity/sequences.json

Find the top repeated sequence.
Generate ONE macro:
    python tools/build_macro.py --sequence <top_id>

Close computer.

---

## WEEKLY (ONCE)
Run:
    python tools/build_bypass_map.py

Open:
    docs/BYPASS_MAP.md

Wrap ONE item with COMMIT_ACTION.
Not two. Not redesign. One.

---

## RULES
- Do not add features during this period.
- Do not redesign.
- Do not optimize.
- Only:
  start → work → run 3 commands → create 1 macro.

This trains SWARMZ using real behavior, not theory.