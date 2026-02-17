# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Normalization layer to standardize event data.
"""

import json

def normalize_event(event):
    """Normalize an event to ensure consistency."""
    event = event.copy()

    # Normalize file paths
    if "file" in event:
        event["file"] = normalize_file_path(event["file"])

    # Normalize command strings
    if "command" in event:
        event["command"] = normalize_command(event["command"])

    # Normalize error messages
    if "error_message" in event:
        event["error_message"] = hash(event["error_message"])

    return event

def normalize_file_path(file_path):
    """Convert file paths to repo-relative paths where possible."""
    # Placeholder for actual normalization logic
    return file_path

def normalize_command(command):
    """Tokenize command strings into arrays."""
    return command.split()

