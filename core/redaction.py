# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Redaction + Privacy Guard layer to ensure sensitive data is protected.
"""

import re

REDACTION_RULES = {
    "tokens": r"[A-Za-z0-9]{32,}",
    "emails": r"[\w.-]+@[\w.-]+",
    "phones": r"\+?\d{10,15}",
}


def redact_event(event):
    """Redact sensitive information from an event."""
    event = event.copy()
    for key, value in event.items():
        if isinstance(value, str):
            for rule_name, pattern in REDACTION_RULES.items():
                value = re.sub(pattern, f"<REDACTED:{rule_name}>", value)
            event[key] = value
    return event
