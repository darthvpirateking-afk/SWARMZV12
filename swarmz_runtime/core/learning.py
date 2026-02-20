# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any
import math


class LearningEngine:
    def __init__(self):
        self.learning_rate = 0.1
        self.decay_rate = 0.1
        self.weights = {}
    
    def update_weights(self, mission_id: str, roi: float):
        current_weight = self.weights.get(mission_id, 0.5)
        new_weight = current_weight + (roi * self.learning_rate)
        new_weight = max(0.0, min(1.0, new_weight))
        
        self.weights[mission_id] = new_weight
        return new_weight
    
    def apply_decay(self, mission_id: str, age_days: float):
        if mission_id not in self.weights:
            return 0.5
        
        current_weight = self.weights[mission_id]
        half_life = 30
        decay_factor = math.exp(-age_days * math.log(2) / half_life)
        
        decayed_weight = current_weight * decay_factor
        self.weights[mission_id] = decayed_weight
        
        return decayed_weight
    
    def get_weight(self, mission_id: str) -> float:
        return self.weights.get(mission_id, 0.5)
    
    def extract_template(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "category": mission.get("category"),
            "goal_pattern": mission.get("goal", "")[:50],
            "constraints": mission.get("constraints", {}),
            "success_indicators": mission.get("success_indicators", {})
        }

