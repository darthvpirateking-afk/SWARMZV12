# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any, List
from swarmz_runtime.storage.db import Database


class ProphetEngine:
    def __init__(self, db: Database):
        self.db = db
        self.failure_patterns = {}
    
    def analyze_failures(self) -> List[Dict[str, Any]]:
        audit = self.db.load_audit_log(limit=1000)
        failures = [e for e in audit if e.get("event_type") == "mission_failed"]
        
        patterns = {}
        for failure in failures[-50:]:
            signature = self._extract_failure_signature(failure)
            patterns[signature] = patterns.get(signature, 0) + 1
        
        self.failure_patterns = patterns
        
        prophecies = []
        for signature, count in patterns.items():
            if count >= 3:
                likelihood = min(0.9, count / 10)
                prophecies.append({
                    "failure_signature": signature,
                    "likelihood": likelihood,
                    "warning": f"Pattern '{signature}' detected {count} times",
                    "recommended_action": "Review constraints or mission design"
                })
        
        return sorted(prophecies, key=lambda x: x["likelihood"], reverse=True)
    
    def _extract_failure_signature(self, failure: Dict[str, Any]) -> str:
        details = failure.get("details", {})
        reason = details.get("reason", "unknown")
        category = details.get("category", "unknown")
        return f"{category}:{reason}"
    
    def predict_failure_risk(self, mission: Dict[str, Any]) -> float:
        category = mission.get("category", "forge")
        signature = f"{category}:resource_limit"
        
        count = self.failure_patterns.get(signature, 0)
        return min(0.8, count / 10)

