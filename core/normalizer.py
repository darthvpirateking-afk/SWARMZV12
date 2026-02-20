
# MIT License
# Copyright (c) 2026 SWARMZ
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Implements the Normalization layer to standardize event data.
"""


import json
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

