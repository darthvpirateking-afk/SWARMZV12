# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Promotion Switch layer to manage enforcement modes.
"""

import json

CONFIG_PATH = "config/enforcement.json"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_mode():
    config = load_config()
    return config.get("mode", "OBSERVE")

def should_enforce(action_class):
    config = load_config()
    return config["enabled"] and action_class in config["enforce_on"]

def handle_violation(action_class, reason):
    mode = get_mode()
    if mode == "OBSERVE":
        return {"allow": True, "reason": "OBSERVE mode: no enforcement"}
    elif mode == "WARN":
        print(f"WARNING: {reason}")
        return {"allow": True, "reason": "WARN mode: warning issued"}
    elif mode == "ENFORCE":
        return {"allow": False, "reason": "ENFORCE mode: action blocked"}
    return {"allow": True, "reason": "Unknown mode"}
