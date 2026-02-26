import time
import logging
from typing import Dict, Any
from enum import Enum
from core.telemetry import telemetry

logger = logging.getLogger(__name__)

class CognitiveState(Enum):
    OPTIMAL = "OPTIMAL"      # All systems nominal, low error rate
    CAUTIOUS = "CAUTIOUS"    # Recent non-critical errors, slower execution
    RESTRICTED = "RESTRICTED" # Security alerts or high error rates, certain domains disabled
    CRITICAL = "CRITICAL"    # System integrity compromised, emergency lockdown

class SystemReflector:
    """
    A self-awareness component that reflects on system performance 
    and dictates meta-policies based on historical telemetry.
    """
    
    def __init__(self, observation_window_seconds: int = 3600):
        self.observation_window = observation_window_seconds
        self.last_reflect_time = 0
        self._cached_state = CognitiveState.OPTIMAL
        self._metrics = {}

    def reflect(self) -> CognitiveState:
        """
        Analyzes the last N seconds of telemetry and capability status.
        Returns the overall CognitiveState.
        """
        now = time.time()
        # Only reflect every 30 seconds to avoid overhead
        if now - self.last_reflect_time < 30:
            return self._cached_state
            
        logs = telemetry.get_recent_logs()
        recent_logs = [l for l in logs if now - l.get("timestamp", 0) < self.observation_window]
        
        critical_count = len([l for l in recent_logs if l.get("level") == "CRITICAL"])
        error_count = len([l for l in recent_logs if l.get("level") == "ERROR"])
        warning_count = len([l for l in recent_logs if l.get("level") == "WARNING"])
        
        # Calculate error density (errors per log)
        total_logs = len(recent_logs)
        error_density = error_count / total_logs if total_logs > 0 else 0
        
        # Determine State
        if critical_count > 0:
            state = CognitiveState.CRITICAL
        elif error_density > 0.2 or error_count > 10:
            state = CognitiveState.RESTRICTED
        elif error_density > 0.05 or warning_count > 5:
            state = CognitiveState.CAUTIOUS
        else:
            state = CognitiveState.OPTIMAL
            
        self._cached_state = state
        self._last_reflect_time = now
        self._metrics = {
            "total_logs": total_logs,
            "critical": critical_count,
            "error_density": round(error_density, 2),
            "warnings": warning_count
        }
        
        logger.info(f"SYSTEM REFLECTION: State is {state.value}. Metrics: {self._metrics}")
        return state

    def get_cognition_summary(self) -> Dict[str, Any]:
        """Provides a JSON-serializable summary of the system's self-awareness."""
        return {
            "state": self._cached_state.value,
            "timestamp": time.time(),
            "metrics": self._metrics,
            "stable": self._cached_state in [CognitiveState.OPTIMAL, CognitiveState.CAUTIOUS]
        }

# Global singleton
reflector = SystemReflector()
