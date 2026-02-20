# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# SWARMZ Session Timer Engine
# Purpose: Track active, idle, focused, and loop time.

import json

class SessionTimer:
    def __init__(self):
        self.timers = {"active": 0, "idle": 0, "focused": 0, "loop": 0}

    def tick(self):
        try:
            self.timers["active"] += 1
        except Exception as e:
            pass  # Fail-open: Skip on error

    def get_timer_state(self):
        return self.timers

    def reset_daily(self):
        self.timers = {"active": 0, "idle": 0, "focused": 0, "loop": 0}
        try:
            with open("data/context/timer.json", "w") as f:
                json.dump(self.timers, f)
        except Exception as e:
            pass  # Fail-open
