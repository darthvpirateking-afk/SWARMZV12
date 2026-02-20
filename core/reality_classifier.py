
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
        if fnmatch.fnmatchcase(action_name, pattern) or fnmatch.fnmatch(action_name, pattern):
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
