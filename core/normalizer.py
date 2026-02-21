# SWARMZ Proprietary License
# Copyright (c) 2026 SWARMZ. All Rights Reserved.
#
# This software is proprietary and confidential to SWARMZ.
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Authorized SWARMZ developers may modify this file solely for contributions
# to the official SWARMZ repository. See LICENSE for full terms.

"""
Implements the Normalization layer to standardize event data.
"""

import hashlib


def normalize_event(event):
    """Normalize an event to ensure consistency."""
    event = event.copy()

    # Normalize file paths
    if "file" in event:
        event["file"] = normalize_file_path(event["file"])

    # Normalize command strings
    if "command" in event:
        event["command"] = normalize_command(event["command"])

    # Normalize error messages using a stable hash
    if "error_message" in event:
        event["error_message"] = stable_hash(event["error_message"])


def stable_hash(value: str) -> str:
    """Return a stable SHA256 hash for a string value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

    return event


def normalize_file_path(file_path):
    """Convert file paths to repo-relative paths where possible."""
    # Placeholder for actual normalization logic
    return file_path


def normalize_command(command):
    """Tokenize command strings into arrays."""
    return command.split()
