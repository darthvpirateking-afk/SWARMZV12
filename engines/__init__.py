# SWARMZ V3.0 Engine Framework
# Multi-engine backend for the governed AI organism

from .base_engine import BaseEngine, EngineType, EngineState, EngineMessage, EngineManager
from .intelligence_engine import IntelligenceEngine
# TODO: Implement remaining engines
# from .mission_engine import MissionEngine
# from .evolution_engine import EvolutionEngine
# from .system_engine import SystemEngine
# from .admin_engine import AdminEngine
# from .chat_engine import ChatEngine
# from .synthetic_engine import SyntheticEngine

__all__ = [
    'BaseEngine',
    'EngineType', 
    'EngineState',
    'EngineMessage',
    'EngineManager',
    'IntelligenceEngine',
    # TODO: Add when implemented
    # 'MissionEngine',
    # 'EvolutionEngine', 
    # 'SystemEngine',
    # 'AdminEngine',
    # 'ChatEngine',
    # 'SyntheticEngine'
]

# Global engine manager instance
engine_manager = EngineManager()

# Register available engines
try:
    from .intelligence_engine import IntelligenceEngine
    intelligence_engine = IntelligenceEngine()
    # Note: Registration happens via async initialize() call
    engine_manager.engines[EngineType.INTELLIGENCE] = intelligence_engine
except Exception as e:
    print(f"Warning: Could not register Intelligence Engine: {e}")