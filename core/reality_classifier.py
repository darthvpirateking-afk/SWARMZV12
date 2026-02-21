# SWARMZ Proprietary License
# Copyright (c) 2026 SWARMZ. All Rights Reserved.
#
# This software is proprietary and confidential to SWARMZ.
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Authorized SWARMZ developers may modify this file solely for contributions
# to the official SWARMZ repository. See LICENSE for full terms.

"""
Implements the Reality Classifier layer to categorize actions based on risk.
"""

import json
import logging
import fnmatch

logging.basicConfig(level=logging.DEBUG)

CONFIG_PATH = "config/reality_classifier.json"


def load_classifier_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def classify_action(action_name):
    config = load_classifier_config()
    logging.debug(f"Loaded config: {config}")
    for rule in config["rules"]:
        pattern = rule["pattern"]
        # Use fnmatchcase for strict matching, fallback to fnmatch for compatibility
        if fnmatch.fnmatchcase(action_name, pattern) or fnmatch.fnmatch(
            action_name, pattern
        ):
            logging.debug(f"Matched rule: {rule}")
            return config["classifiers"].get(rule["class"], "ALLOW")
    logging.debug("No matching rule found. Defaulting to ALLOW.")
    return "ALLOW"


def handle_action(action_name):
    classification = classify_action(action_name)
    if classification == "ALLOW":
        return {"allow": True, "reason": "Action allowed by default"}
    elif classification == "WARN":
        print(f"WARNING: Action '{action_name}' is high risk.")
        return {"allow": True, "reason": "High risk action, warning issued"}
    elif classification == "BLOCK":
        return {"allow": False, "reason": "Critical action blocked"}
    return {"allow": True, "reason": "Unknown classification"}
