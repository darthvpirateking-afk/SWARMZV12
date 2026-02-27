# NEXUSMON OPERATOR PACK — COMPLETE WORKFLOW

## DAILY START (RITUAL A)
1. Run:
       python tools/verify_activity_stream.py
2. If entries appear → continue working.
   If empty → restart NEXUSMON.

---

## DAILY END (RITUAL B)
1. Run in order:
       python tools/normalize_events.py
       python tools/mine_sequences.py
       python tools/value_report.py
2. Open:
       data/activity/sequences.json
3. Find the top repeated sequence.
4. Generate ONE macro:
       python tools/build_macro.py --sequence <top_id>
5. Close computer.

---

## WEEKLY RITUAL
1. Run:
       python tools/build_bypass_map.py
2. Open:
       docs/BYPASS_MAP.md
3. Wrap ONE item with COMMIT_ACTION.
   Not two. Not redesign. One.

---

## DISCIPLINE RULES
- Do not add features during this period.
- Do not redesign.
- Do not optimize.
- Only:
  start → work → run 3 commands → create 1 macro.

This ensures NEXUSMON learns from real behavior, not theory.
