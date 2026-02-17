# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Reality Classifier layer to categorize actions based on risk.
"""

import json
import logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_PATH = "config/reality_classifier.json"

def load_classifier_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def classify_action(action_name):
    config = load_classifier_config()
    logging.debug(f"Loaded config: {config}")
    for rule in config["rules"]:
        if action_name.endswith(rule["pattern"]):
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
