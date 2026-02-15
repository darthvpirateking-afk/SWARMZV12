from typing import Dict, Any
from datetime import datetime, timedelta


class VisibilityManager:
    def __init__(self):
        self.levels = {
            "dim": 0,
            "visible": 1,
            "bright": 2,
            "ultraviolet": 3
        }
    
    def should_log(self, event_level: str, current_level: str = "visible") -> bool:
        event_val = self.levels.get(event_level, 1)
        current_val = self.levels.get(current_level, 1)
        return event_val >= current_val
    
    def filter_events(self, events: list, visibility_level: str = "visible") -> list:
        return [e for e in events if self.should_log(e.get("visibility", "visible"), visibility_level)]
