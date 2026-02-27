# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Bypass map layer.

Identifies simple execution bypass candidates from event stream data.
"""

from typing import Any, Dict, Iterable, List


def build_bypass_map(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event") == "bypass":
            results.append(event)
    return results
