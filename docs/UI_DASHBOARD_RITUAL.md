# NEXUSMON UI — DAILY OPERATOR FLOW

## START SESSION
🟢 Press “VERIFY STREAM”
Runs: tools/verify_activity_stream.py  
If green → continue  
If red → restart NEXUSMON

---

## END SESSION
🟡 Press “PROCESS DAY”
Runs:
- normalize_events
- mine_sequences
- value_report

Then UI shows:
- Top repeated sequence
- “Generate Macro” button

---

## WEEKLY
🔵 Press “BUILD BYPASS MAP”
Then UI opens docs/BYPASS_MAP.md  
Choose ONE item → wrap with COMMIT_ACTION

---

## DONE
Close laptop. NEXUSMON learns from repetition.
