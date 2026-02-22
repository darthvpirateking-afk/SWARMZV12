"""
SWARMZ V3.0 Base Engine Framework
Core abstraction for all SWARMZ engines with deterministic, auditable behavior
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
import uuid
import json
from datetime import datetime
# Simple logging setup (replaced structlog for compatibility)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EngineType(Enum):
    """All available engine types in SWARMZ V3.0"""
    INTELLIGENCE = "intelligence"
    MISSION = "mission"
    EVOLUTION = "evolution"
    SYSTEM = "system"
    ADMIN = "admin"
    CHAT = "chat"
    SYNTHETIC = "synthetic"

class EngineState(Enum):
    """Engine operational states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class OperatorMode(Enum):
    """Operator sovereignty modes"""
    SOVEREIGN = "sovereign"     # Full operator control
    ASSISTED = "assisted"       # AI assistance with oversight
    AUTONOMOUS = "autonomous"   # Limited autonomous operation
    LOCKED = "locked"          # Emergency lockdown

@dataclass
class EngineMessage:
    """Standard message format between engines"""
    id: str
    source_engine: EngineType
    target_engine: EngineType
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    operator_id: Optional[str] = None
    priority: int = 5  # 1-10, 10 = highest

class ThroneProtocol(Protocol):
    """Throne Layer sovereignty interface - all engines must implement"""
    def receive_throne_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct operator override command"""
        ...
        
    def get_sovereignty_status(self) -> Dict[str, Any]:
        """Return current operator control status"""
        ...

class BaseEngine(ABC):
    """
    Abstract base class for all SWARMZ V3.0 engines
    Enforces deterministic, auditable, operator-controlled behavior
    """
    
    def __init__(self, engine_type: EngineType):
        self.engine_type = engine_type
        self.state = EngineState.INITIALIZING
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.operator_mode = OperatorMode.SOVEREIGN
        self.audit_log: List[Dict] = []
        self.health_metrics: Dict[str, Any] = {}
        self.sovereign_overrides: Dict[str, Any] = {}
        
        logger.info(f"🔧 Initializing {engine_type.value} engine")

    async def initialize(self) -> bool:
        """Initialize engine with full audit trail"""
        try:
            await self._initialize_engine()
            self.state = EngineState.ACTIVE
            self._log_audit("engine_initialized", {"engine": self.engine_type.value})
            logger.info(f"✅ {self.engine_type.value} engine active")
            return True
        except Exception as e:
            self.state = EngineState.OFFLINE
            self._log_audit("engine_failed", {"engine": self.engine_type.value, "error": str(e)})
            logger.error(f"❌ {self.engine_type.value} engine failed: {e}")
            return False

    @abstractmethod
    async def _initialize_engine(self):
        """Engine-specific initialization - implement in subclasses"""
        pass

    async def process_message(self, message: EngineMessage) -> Optional[EngineMessage]:
        """Process message with full sovereignty and audit"""
        
        # Log message receipt
        self._log_audit("message_received", {
            "message_id": message.id,
            "from": message.source_engine.value,
            "type": message.message_type,
            "priority": message.priority
        })
        
        # Check operator sovereignty
        if not self._check_operator_authorization(message):
            self._log_audit("message_rejected", {
                "message_id": message.id,
                "reason": "operator_authorization_failed"
            })
            return None
        
        try:
            # Route to handler
            response = await self._handle_message(message)
            
            # Log successful processing
            self._log_audit("message_processed", {
                "message_id": message.id,
                "response_generated": response is not None
            })
            
            return response
            
        except Exception as e:
            # Log error with context
            self._log_audit("message_error", {
                "message_id": message.id,
                "error": str(e),
                "payload_type": message.message_type
            })
            logger.error(f"Error in {self.engine_type.value}: {e}")
            return None

    @abstractmethod
    async def _handle_message(self, message: EngineMessage) -> Optional[EngineMessage]:
        """Engine-specific message handling"""
        pass

    def receive_throne_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct operator override command (Throne Protocol)"""
        
        self._log_audit("throne_command", {
            "command": command,
            "params": list(params.keys())  # Log param keys, not values for security
        })
        
        # Process sovereignty commands
        if command == "set_operator_mode":
            return self._set_operator_mode(OperatorMode(params["mode"]))
        elif command == "force_state":
            return self._force_engine_state(EngineState(params["state"]))
        elif command == "override_setting":
            return self._set_sovereign_override(params["key"], params["value"])
        elif command == "emergency_stop":
            return self._emergency_stop()
        else:
            return self._handle_custom_throne_command(command, params)

    def _set_operator_mode(self, mode: OperatorMode) -> Dict[str, Any]:
        """Set operator control mode"""
        old_mode = self.operator_mode
        self.operator_mode = mode
        
        self._log_audit("operator_mode_changed", {
            "old_mode": old_mode.value,
            "new_mode": mode.value
        })
        
        return {"status": "success", "old_mode": old_mode.value, "new_mode": mode.value}

    def _force_engine_state(self, state: EngineState) -> Dict[str, Any]:
        """Force engine into specific state (operator override)"""
        old_state = self.state
        self.state = state
        
        self._log_audit("state_forced", {
            "old_state": old_state.value,
            "new_state": state.value
        })
        
        return {"status": "success", "old_state": old_state.value, "new_state": state.value}

    def _set_sovereign_override(self, key: str, value: Any) -> Dict[str, Any]:
        """Set operator override for any engine parameter"""
        self.sovereign_overrides[key] = value
        
        self._log_audit("sovereign_override", {
            "key": key,
            "value_type": type(value).__name__
        })
        
        return {"status": "success", "override_count": len(self.sovereign_overrides)}

    def _emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop - immediate safe state"""
        self.state = EngineState.MAINTENANCE
        self.operator_mode = OperatorMode.LOCKED
        
        self._log_audit("emergency_stop", {"reason": "operator_command"})
        
        return {"status": "emergency_stop_engaged"}

    def _handle_custom_throne_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses for engine-specific throne commands"""
        return {"status": "error", "message": f"Unknown throne command: {command}"}

    def get_health_status(self) -> Dict[str, Any]:
        """Return comprehensive health status"""
        return {
            "engine_type": self.engine_type.value,
            "state": self.state.value,
            "operator_mode": self.operator_mode.value,
            "queue_size": self.message_queue.qsize(),
            "sovereign_overrides": len(self.sovereign_overrides),
            "audit_entries": len(self.audit_log),
            "uptime": self._calculate_uptime(),
            "metrics": self.health_metrics
        }

    def get_sovereignty_status(self) -> Dict[str, Any]:
        """Return operator sovereignty status"""
        return {
            "operator_mode": self.operator_mode.value,
            "sovereign_overrides": list(self.sovereign_overrides.keys()),
            "throne_commands_accepted": True,
            "emergency_stop_available": True,
            "audit_entries": len(self.audit_log)
        }

    def _check_operator_authorization(self, message: EngineMessage) -> bool:
        """Check if message is authorized by current operator mode"""
        
        # In LOCKED mode, only throne commands allowed
        if self.operator_mode == OperatorMode.LOCKED:
            return message.message_type == "throne_command"
        
        # In SOVEREIGN mode, operator approval required for autonomous actions
        if self.operator_mode == OperatorMode.SOVEREIGN:
            return message.operator_id is not None
        
        # Other modes allow more autonomous operation
        return True

    def _log_audit(self, action: str, details: Dict[str, Any]):
        """Add immutable audit log entry"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "engine": self.engine_type.value,
            "action": action,
            "details": details,
            "id": str(uuid.uuid4()),
            "operator_mode": self.operator_mode.value
        }
        
        self.audit_log.append(audit_entry)
        logger.info(f"🔍 AUDIT: {action} - {json.dumps(audit_entry)}")

    def _calculate_uptime(self) -> float:
        """Calculate engine uptime in seconds"""
        # Implementation would track initialization time
        return 0.0  # Placeholder


class EngineManager:
    """
    Central coordination for all SWARMZ V3.0 engines
    Manages inter-engine communication and throne layer sovereignty
    """
    
    def __init__(self):
        self.engines: Dict[EngineType, BaseEngine] = {}
        self.message_bus: asyncio.Queue = asyncio.Queue()
        self.throne_active = False
        self.operator_id: Optional[str] = None
        self.messages_processed = 0
        
        logger.info("👑 Engine Manager initialized")

    async def initialize(self) -> bool:
        """Initialize all registered engines"""
        logger.info("🚀 Initializing Engine Manager...")
        
        # Initialize all engines
        for engine_type, engine in self.engines.items():
            try:
                success = await engine.initialize()
                if not success:
                    logger.error(f"❌ Failed to initialize {engine_type.value}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error initializing {engine_type.value}: {e}")
                return False
        
        logger.info("✅ Engine Manager initialization complete")
        return True

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "throne_active": self.throne_active,
            "operator_id": self.operator_id,
            "total_engines": len(self.engines),
            "engines": {
                engine_type.value: {
                    "state": engine.state.value if hasattr(engine, 'state') else "UNKNOWN",
                    "health": engine.get_health_status() if hasattr(engine, 'get_health_status') else {"status": "unknown"}
                }
                for engine_type, engine in self.engines.items()
            }
        }

    async def route_message(self, message: EngineMessage) -> Optional[EngineMessage]:
        """Route message to target engine"""
        self.messages_processed += 1
        return await self.send_message(message)

    async def throne_command(self, operator_id: str, command: str, target_engine: Optional[EngineType] = None, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute throne layer command"""
        self.operator_id = operator_id
        params = parameters or {}
        return self.execute_throne_command(command, params, target_engine)

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status"""
        active_engines = sum(1 for engine in self.engines.values() if getattr(engine, 'state', None) == EngineState.ACTIVE)
        
        return {
            "overall_status": "HEALTHY" if active_engines > 0 else "NO_ENGINES",
            "active_engines": active_engines,
            "total_engines": len(self.engines),
            "messages_processed": self.messages_processed,
            "throne_active": self.throne_active
        }

    async def register_engine(self, engine: BaseEngine) -> bool:
        """Register engine with sovereignty checks"""
        try:
            success = await engine.initialize()
            if success:
                self.engines[engine.engine_type] = engine
                logger.info(f"✅ {engine.engine_type.value} engine registered")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to register {engine.engine_type.value}: {e}")
            return False

    async def send_message(self, message: EngineMessage) -> Optional[EngineMessage]:
        """Send message through sovereignty layer"""
        target_engine = self.engines.get(message.target_engine)
        if not target_engine:
            logger.error(f"❌ Engine {message.target_engine.value} not found")
            return None
        
        return await target_engine.process_message(message)

    def execute_throne_command(self, command: str, params: Dict[str, Any], target_engine: Optional[EngineType] = None) -> Dict[str, Any]:
        """Execute throne layer command with absolute sovereignty"""
        
        if target_engine:
            # Command specific engine
            engine = self.engines.get(target_engine)
            if engine:
                return engine.receive_throne_command(command, params)
            else:
                return {"status": "error", "message": f"Engine {target_engine.value} not found"}
        else:
            # Command all engines
            results = {}
            for engine_type, engine in self.engines.items():
                results[engine_type.value] = engine.receive_throne_command(command, params)
            return {"status": "broadcast_complete", "results": results}

    def get_global_health(self) -> Dict[str, Any]:
        """Get system-wide health and sovereignty status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "throne_active": self.throne_active,
            "operator_id": self.operator_id,
            "total_engines": len(self.engines),
            "engines": {
                engine_type.value: engine.get_health_status()
                for engine_type, engine in self.engines.items()
            }
        }


# Global engine manager instance
engine_manager = EngineManager()