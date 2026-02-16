# SWARMZ Data Storage: JSONL Format and Bad Row Handling

## JSONL Format
- All mission and audit logs are stored in the `data/` directory as `.jsonl` (JSON Lines) files.
- Each line is a single valid JSON object.
- Blank lines or lines with only whitespace are ignored by the system.

## Bad Row Handling
- If a line in a `.jsonl` file is not valid JSON, it is skipped and moved to `data/bad_rows.jsonl` for quarantine.
- The system logs a warning for each bad row encountered.
- The `/v1/debug/storage_check` endpoint reports the number of parsed, skipped, and quarantined rows.

## Atomic Writes
- All writes to `.jsonl` files are done atomically: each new record is appended as a single line using compact JSON.

## Recovery
- If a `.jsonl` file contains blank or malformed lines, the server will not crash. Instead, it will continue operation and report the issue via the debug endpoint.

---
For more details, see the implementation in `swarmz_runtime/storage/db.py` and the `/v1/debug/storage_check` endpoint.
