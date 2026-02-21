# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Evidence Pack layer to bundle shareable proof for claims.
"""


def create_evidence_pack(claim, events, stats, suggested_fix):
    """Create an evidence pack for a given claim."""
    return {
        "claim": claim,
        "supporting_event_ids": [event["event_id"] for event in events],
        "key_excerpts": [event.get("excerpt", "") for event in events],
        "timestamps": [event["timestamp"] for event in events],
        "computed_stats": stats,
        "suggested_fix_path": suggested_fix,
        "confidence": "high",
    }
