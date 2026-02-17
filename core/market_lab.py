# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Market Lab Module

Provides deterministic backtesting over local CSV data.
"""

from typing import Dict, Any, List
from pathlib import Path
import csv
import json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MARKET_LOG = DATA_DIR / "market_lab.jsonl"


def backtest_strategy(csv_path: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Run a deterministic backtest over the given CSV data."""
    results = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Apply strategy logic (example: filter rows)
                if strategy.get("filter") in row.get("category", ""):
                    results.append(row)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "results": results, "count": len(results)}


def self_check() -> Dict[str, Any]:
    """Perform a lightweight self-check of the Market Lab module."""
    return {
        "ok": True,
        "market_log_exists": MARKET_LOG.exists(),
    }
