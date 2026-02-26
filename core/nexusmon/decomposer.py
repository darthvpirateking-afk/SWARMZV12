"""
NEXUSMON Decomposer (P2.3)

Translates high-level mission intents into a validated DAG of tasks
for the MissionEngine to execute. Uses rules + domain knowledge.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class NexusmonDecomposer:
    """Specialized decomposer for Sovereign/Nexusmon-class missions."""
    
    def decompose(self, mission_id: str, intent: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decomposes an intent into a list of task definitions.
        Each task: {id, dependencies, capability_id, params}
        """
        tasks = []
        intent_lower = intent.lower()
        
        # Domain: Bio Lab
        if any(word in intent_lower for word in ["bio", "crispr", "protein", "dna", "sequence"]):
            tasks = self._decompose_bio(intent_lower, spec)
        
        # Domain: Space Mission
        elif any(word in intent_lower for word in ["space", "orbital", "satellite", "telemetry", "burn"]):
            tasks = self._decompose_space(intent_lower, spec)
            
        # Default: Kernel / General Sovereign
        else:
            tasks = [
                {
                    "id": "verify_intent",
                    "dependencies": [],
                    "capability_id": "kernel_base",
                    "params": {"action": "VERIFY", "target": intent}
                },
                {
                    "id": "sovereign_audit",
                    "dependencies": ["verify_intent"],
                    "capability_id": "kernel_base",
                    "params": {"action": "AUDIT", "target": "execution_readiness"}
                }
            ]
            
        logger.info(f"Decomposed mission {mission_id} into {len(tasks)} tasks.")
        return tasks

    def _decompose_bio(self, intent: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Strategy for bio-mission decomposition."""
        # Example: "Verify CRISPR sequence XYZ"
        seq_id = spec.get("sequence_id", "GENERIC_001")
        
        return [
            {
                "id": "sequence_load",
                "dependencies": [],
                "capability_id": "bio_lab_api",
                "params": {"action": "SYNTHETIC_SEQUENCE_LOAD", "sequence_id": seq_id}
            },
            {
                "id": "crispr_verify",
                "dependencies": ["sequence_load"],
                "capability_id": "bio_lab_api",
                "params": {"action": "CRISPR_SEQUENCE_VERIFY", "sequence_id": seq_id}
            },
            {
                "id": "fold_simulation",
                "dependencies": ["crispr_verify"],
                "capability_id": "bio_lab_api",
                "params": {"action": "PROTEIN_FOLD_SIM", "sequence_id": seq_id}
            }
        ]

    def _decompose_space(self, intent: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Strategy for space-mission decomposition."""
        target = spec.get("target", "NEXUS-SAT-1")
        
        return [
            {
                "id": "orbital_sync",
                "dependencies": [],
                "capability_id": "space_mission_control",
                "params": {"action": "KEPLER_EL_SYNC", "target": target}
            },
            {
                "id": "trajectory_verify",
                "dependencies": ["orbital_sync"],
                "capability_id": "space_mission_control",
                "params": {"action": "OBSERVE", "target": target}
            }
        ]
