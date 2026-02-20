# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any, List
from swarmz_runtime.storage.db import Database


class ResonanceDetector:
    def __init__(self, db: Database):
        self.db = db
        self.thresholds = {
            1: "ignore",
            3: "warn",
            7: "intervene",
            13: "lock"
        }
    
    def detect_pattern(self, pattern: str) -> Dict[str, Any]:
        count = self.db.increment_pattern_counter(pattern)
        action = self._get_action(count)
        
        return {
            "pattern": pattern,
            "frequency": count,
            "threshold": self._get_threshold(count),
            "action": action
        }
    
    def _get_action(self, count: int) -> str:
        if count >= 13:
            return "lock"
        elif count >= 7:
            return "intervene"
        elif count >= 3:
            return "warn"
        else:
            return "ignore"
    
    def _get_threshold(self, count: int) -> int:
        for threshold in sorted(self.thresholds.keys(), reverse=True):
            if count >= threshold:
                return threshold
        return 1
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        state = self.db.load_state()
        counters = state.get("pattern_counters", {})
        
        patterns = []
        for pattern, count in counters.items():
            patterns.append({
                "pattern": pattern,
                "frequency": count,
                "threshold": self._get_threshold(count),
                "action": self._get_action(count)
            })
        
        return sorted(patterns, key=lambda x: x["frequency"], reverse=True)

