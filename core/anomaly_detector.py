# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Anomaly detector layer.

Detects simple deviations in event sequences for downstream tooling.
"""

from typing import Any, Dict, Iterable, List


def detect_anomalies(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    anomalies: List[Dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            anomalies.append({"reason": "non-dict-event", "event": str(event)})
            continue
        if "event" not in event:
            anomalies.append({"reason": "missing-event-key", "event": event})
    return anomalies
