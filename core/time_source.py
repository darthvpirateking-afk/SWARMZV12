# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/time_source.py â€” Deterministic time helpers for SWARMZ.

All times are UTC ISOâ€‘8601 strings (with trailing Z).
Centralised so every module uses the same format.
"""

from datetime import datetime, timezone


def now() -> str:
    """Return current UTC timestamp in ISOâ€‘8601 format with trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def today() -> str:
    """Return current UTC date as YYYYâ€‘MMâ€‘DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def mission_timestamp() -> str:
    """Return a compact msâ€‘precision timestamp suitable for mission IDs."""
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))

