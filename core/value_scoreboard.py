# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Value Scoreboard layer to track and report value metrics.
"""

import json

SCOREBOARD_PATH = "data/value_scoreboard.json"

def load_scoreboard():
    try:
        with open(SCOREBOARD_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def update_scoreboard(metric, value):
    scoreboard = load_scoreboard()
    scoreboard[metric] = scoreboard.get(metric, 0) + value
    with open(SCOREBOARD_PATH, "w") as f:
        json.dump(scoreboard, f, indent=4)

def get_top_metrics(limit=5):
    scoreboard = load_scoreboard()
    return sorted(scoreboard.items(), key=lambda x: x[1], reverse=True)[:limit]
