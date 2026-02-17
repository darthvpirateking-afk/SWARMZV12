# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
JSONL utilities for robust reading/writing of JSON Lines format.
Handles blank lines, malformed JSON, and quarantines bad rows.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_jsonl(filepath: Path) -> Tuple[List[Dict], int, int]:
    """
    Robustly read a JSONL file, skipping blank/whitespace-only lines.
    
    Args:
        filepath: Path to .jsonl file
        
    Returns:
        Tuple of (list of dicts, count of skipped empty lines, count of quarantined bad rows)
    """
    if not filepath.exists():
        return [], 0, 0
    
    rows = []
    skipped_count = 0
    quarantined_count = 0
    bad_rows_file = filepath.parent / "bad_rows.jsonl"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.rstrip("\n\r")
                
                # Skip blank/whitespace-only lines
                if not line or not line.strip():
                    skipped_count += 1
                    continue
                
                # Try to parse JSON
                try:
                    obj = json.loads(line)
                    rows.append(obj)
                except json.JSONDecodeError as e:
                    # Quarantine bad row
                    quarantined_count += 1
                    logger.warning(f"Bad JSON on line {line_no} of {filepath.name}: {e}")
                    
                    # Append to bad_rows.jsonl
                    bad_entry = {
                        "source_file": filepath.name,
                        "line_number": line_no,
                        "error": str(e),
                        "bad_line": line[:200],  # Truncate for safety
                        "quarantined_at": datetime.utcnow().isoformat() + "Z"
                    }
                    try:
                        with open(bad_rows_file, "a", encoding="utf-8") as bf:
                            bf.write(json.dumps(bad_entry, separators=(",", ":")) + "\n")
                    except Exception as write_err:
                        logger.error(f"Failed to write to bad_rows.jsonl: {write_err}")
    
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
    
    return rows, skipped_count, quarantined_count


def write_jsonl(filepath: Path, obj: Dict[str, Any]) -> None:
    """
    Atomically append a JSON object to a JSONL file.
    
    Args:
        filepath: Path to .jsonl file
        obj: Dictionary to write as JSON
    """
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON atomically (append mode)
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to {filepath}: {e}")
        raise

