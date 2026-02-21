# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import hashlib
import json
import numpy as np

# Avoid circular import - will be set by the engine
_engine_instance = None


def set_engine_provider(engine_provider: Callable):
    """Set the engine provider function to avoid circular imports."""
    global _engine_instance
    _engine_instance = engine_provider


def get_engine():
    """Get the engine instance."""
    if _engine_instance is None:
        raise ValueError("Engine instance is not set")
    return _engine_instance


class NextTaskMatrix:
    """
    NEXT TASK MATRIX
    ────────────────
    Control surface for UI → runtime bridge ignition-phase architecture.

    Layer Mappings & Weighted Hierarchy:
    1. THE THING WITHOUT A NAME (1.00) → sovereignty
    2. HIDDEN WAY (0.92) → override
    3. MYTHICAL WAY (0.88) → alignment
    4. MAGIC WAY (0.85) → uplift
    5. ARCHITECTURAL RESTRAINT (0.82) → purity
    6. SPACE-SHAPING (0.79) → direction
    7. PRE-EVALUATED (0.76) → filtration
    8. UNIVERSAL GIFT (0.73) → integration
    9. STABILIZING (0.70) → continuity

    OUTPUT: unified ignition-state vector for cockpit operations
    """

    def __init__(self, engine_provider: Callable = None):
        if engine_provider:
            set_engine_provider(engine_provider)

        # Layer weights and processing order (highest to lowest priority)
        self.layer_weights = {
            "sovereign_arbitration": 1.00,  # THE THING WITHOUT A NAME → sovereignty
            "override": 0.92,  # HIDDEN WAY → override
            "alignment": 0.88,  # MYTHICAL WAY → alignment
            "uplift": 0.85,  # MAGIC WAY → uplift
            "boundary": 0.82,  # ARCHITECTURAL RESTRAINT → purity
            "geometry": 0.79,  # SPACE-SHAPING → direction
            "filtration": 0.76,  # PRE-EVALUATED → filtration
            "integration": 0.73,  # UNIVERSAL GIFT → integration
            "continuity": 0.70,  # STABILIZING → continuity
        }

        # Deterministic processing order by weight (highest first)
        self.layer_order = sorted(
            self.layer_weights.keys(), key=lambda x: self.layer_weights[x], reverse=True
        )

        # Initialize evaluation layers
        self.layers = {
            "filtration": PreEvaluatedLayer(),
            "geometry": SpaceShapingLayer(),
            "boundary": ArchitecturalRestraintLayer(),
            "alignment": MythicalWayLayer(),
            "override": HiddenWayLayer(),
            "uplift": MagicWayLayer(),
            "sovereign_arbitration": SovereignArbitrationLayer(),
            "integration": UniversalGiftLayer(),
            "continuity": StabilizingLayer(),
        }

    def process_task_matrix(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process through the NEXT TASK MATRIX to generate unified ignition-state vector.

        Returns:
            ignition_state_vector: Dict containing:
                - unified_vector: numpy array of ignition states
                - cockpit_signal: operator-ready signal
                - kernel_path: execution path for kernel operations
                - layer_states: individual layer outputs
                - meta_coherence: final coherence score
        """
        if not options:
            return {"status": "No options provided"}

        layer_states = {}
        current_options = options.copy()

        # Process through each layer in deterministic order
        for layer_name in self.layer_order:
            layer = self.layers[layer_name]
            layer_result = layer.process(context, current_options)
            layer_states[layer_name] = layer_result

            # Update options for next layer (except final arbitration)
            if layer_name != "sovereign_arbitration":
                current_options = layer_result.get("filtered_options", current_options)

        # Generate unified ignition-state vector
        ignition_vector = self._generate_ignition_vector(layer_states)

        # Create cockpit-ready operator signal
        cockpit_signal = self._generate_cockpit_signal(layer_states, ignition_vector)

        # Determine kernel-level execution path
        kernel_path = self._determine_kernel_path(layer_states, ignition_vector)

        return {
            "unified_vector": ignition_vector,
            "cockpit_signal": cockpit_signal,
            "kernel_path": kernel_path,
            "layer_states": layer_states,
            "meta_coherence": layer_states.get("sovereign_arbitration", {}).get(
                "coherence", 0
            ),
            "timestamp": datetime.now().isoformat(),
            "matrix_version": "1.0",
        }

    def _generate_ignition_vector(self, layer_states: Dict[str, Any]) -> np.ndarray:
        """
        Generate unified ignition-state vector from layer states with weighted hierarchy.
        Returns 9-dimensional numpy array representing weighted ignition state.
        """
        vector_components = []

        for layer_name in self.layer_order:
            state = layer_states.get(layer_name, {})
            # Extract scalar ignition value from each layer
            raw_ignition_value = state.get("ignition_value", 0.0)
            # Apply layer weight from hierarchy
            weight = self.layer_weights.get(layer_name, 1.0)
            weighted_value = raw_ignition_value * weight
            vector_components.append(weighted_value)

        return np.array(vector_components, dtype=np.float32)

    def _generate_cockpit_signal(
        self, layer_states: Dict[str, Any], ignition_vector: np.ndarray
    ) -> Dict[str, Any]:
        """
        Generate cockpit-ready operator signal from layer states and ignition vector.
        """
        sovereign_state = layer_states.get("sovereign_arbitration", {})
        coherence = sovereign_state.get("coherence", 0)

        # Determine signal strength based on coherence and vector magnitude
        vector_magnitude = np.linalg.norm(ignition_vector)
        signal_strength = min(1.0, (coherence + vector_magnitude) / 2.0)

        # Determine operational readiness
        operational_readiness = "STANDBY"
        if signal_strength > 0.8:
            operational_readiness = "IGNITION_READY"
        elif signal_strength > 0.5:
            operational_readiness = "SYSTEMS_NOMINAL"
        elif signal_strength > 0.2:
            operational_readiness = "INITIALIZING"

        return {
            "signal_strength": signal_strength,
            "operational_readiness": operational_readiness,
            "vector_magnitude": vector_magnitude,
            "dominant_layer": self._get_dominant_layer(ignition_vector),
            "sovereign_decision": sovereign_state.get("decision", {}),
            "ignition_code": self._generate_ignition_code(signal_strength),
        }

    def _determine_kernel_path(
        self, layer_states: Dict[str, Any], ignition_vector: np.ndarray
    ) -> Dict[str, Any]:
        """
        Determine kernel-level execution path based on ignition state.
        """
        coherence = layer_states.get("sovereign_arbitration", {}).get("coherence", 0)
        vector_max = np.max(ignition_vector)

        # Kernel execution priority based on ignition state
        if coherence > 0.9 and vector_max > 0.8:
            execution_mode = "sovereign_override"
            priority = "critical"
        elif coherence > 0.7 and vector_max > 0.6:
            execution_mode = "deterministic_uplift"
            priority = "high"
        elif coherence > 0.5 and vector_max > 0.4:
            execution_mode = "archetypal_alignment"
            priority = "normal"
        elif coherence > 0.3 and vector_max > 0.2:
            execution_mode = "architectural_constraint"
            priority = "low"
        else:
            execution_mode = "pre_evaluation_filter"
            priority = "background"

        return {
            "execution_mode": execution_mode,
            "priority": priority,
            "kernel_safe": True,  # Always kernel-safe by design
            "requires_sovereign_approval": execution_mode == "sovereign_override",
            "parallel_execution_allowed": priority in ["low", "background"],
        }

    def _get_dominant_layer(self, ignition_vector: np.ndarray) -> str:
        """
        Determine which layer has the highest weighted ignition value.
        """
        max_index = np.argmax(ignition_vector)
        return self.layer_order[max_index]

    def _generate_ignition_code(self, signal_strength: float) -> str:
        """
        Generate ignition code based on signal strength.
        """
        if signal_strength > 0.9:
            return "IGNITION_SEQUENCE_INITIATED"
        elif signal_strength > 0.7:
            return "SYSTEMS_ALIGNMENT_COMPLETE"
        elif signal_strength > 0.5:
            return "ARCHITECTURAL_RESTRAINT_ACTIVE"
        elif signal_strength > 0.3:
            return "GEOMETRIC_BOUNDARIES_ESTABLISHED"
        else:
            return "PRE_EVALUATION_FILTERING"


class PreEvaluatedLayer:
    """FILTRATION: PRE-EVALUATED - Fast filtering layer"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply fast pre-evaluation filtering."""
        filtered = []
        filtered_count = 0

        for option in options:
            if self._passes_pre_evaluation(context, option):
                filtered.append(option)
                filtered_count += 1

        ignition_value = min(1.0, filtered_count / max(1, len(options)))

        return {
            "layer": "filtration",
            "filtered_options": filtered,
            "filtered_count": filtered_count,
            "total_options": len(options),
            "ignition_value": ignition_value,
            "filter_efficiency": filtered_count / max(1, len(options)),
        }

    def _passes_pre_evaluation(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> bool:
        """Fast pre-evaluation check."""
        # Basic validity checks
        if not option.get("id"):
            return False
        if option.get("invalid", False):
            return False
        return True


class SpaceShapingLayer:
    """GEOMETRY: SPACE-SHAPING - Boundary and directional constraints"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply space-shaping geometry constraints."""
        shaped_options = []

        for option in options:
            shaped = self._apply_space_shaping(context, option)
            shaped_options.append(shaped)

        # Calculate geometric coherence
        coherence_sum = sum(opt.get("geometric_coherence", 0) for opt in shaped_options)
        avg_coherence = coherence_sum / max(1, len(shaped_options))

        return {
            "layer": "geometry",
            "shaped_options": shaped_options,
            "geometric_coherence": avg_coherence,
            "ignition_value": avg_coherence,
            "boundary_constraints": len(
                [opt for opt in shaped_options if opt.get("boundary_respected", False)]
            ),
        }

    def _apply_space_shaping(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply geometric space shaping."""
        shaped_option = option.copy()

        # Calculate geometric coherence based on context alignment
        context_domain = context.get("domain", "general")
        option_domain = option.get("domain", "general")

        domain_alignment = 1.0 if context_domain == option_domain else 0.5
        shaped_option["geometric_coherence"] = domain_alignment
        shaped_option["boundary_respected"] = domain_alignment > 0.3

        return shaped_option


class ArchitecturalRestraintLayer:
    """BOUNDARY: ARCHITECTURAL RESTRAINT - Purity enforcement"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply architectural purity constraints."""
        restrained_options = []

        for option in options:
            restrained = self._apply_architectural_restraint(context, option)
            restrained_options.append(restrained)

        purity_scores = [
            opt.get("architectural_purity", 0) for opt in restrained_options
        ]
        avg_purity = sum(purity_scores) / max(1, len(purity_scores))

        return {
            "layer": "boundary",
            "restrained_options": restrained_options,
            "architectural_purity": avg_purity,
            "ignition_value": avg_purity,
            "constraint_violations": len(
                [
                    opt
                    for opt in restrained_options
                    if not opt.get("purity_compliant", True)
                ]
            ),
        }

    def _apply_architectural_restraint(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply architectural purity constraints."""
        restrained_option = option.copy()

        # Check architectural purity
        has_clean_design = not option.get("complex", False)
        follows_patterns = option.get("pattern_compliant", True)
        minimal_implementation = option.get("minimal", True)

        purity_score = (
            has_clean_design + follows_patterns + minimal_implementation
        ) / 3.0
        restrained_option["architectural_purity"] = purity_score
        restrained_option["purity_compliant"] = purity_score > 0.6

        return restrained_option


class MythicalWayLayer:
    """ALIGNMENT: MYTHICAL WAY - Archetypal resonance"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply archetypal alignment."""
        aligned_options = []

        for option in options:
            aligned = self._apply_mythical_alignment(context, option)
            aligned_options.append(aligned)

        resonance_scores = [
            opt.get("archetypal_resonance", 0) for opt in aligned_options
        ]
        avg_resonance = sum(resonance_scores) / max(1, len(resonance_scores))

        return {
            "layer": "alignment",
            "aligned_options": aligned_options,
            "archetypal_resonance": avg_resonance,
            "ignition_value": avg_resonance,
            "mythical_patterns": len(
                [opt for opt in aligned_options if opt.get("pattern_aligned", False)]
            ),
        }

    def _apply_mythical_alignment(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply archetypal pattern alignment."""
        aligned_option = option.copy()

        # Calculate archetypal resonance
        context_archetypes = context.get("archetypes", [])
        option_archetypes = option.get("archetypes", [])

        if context_archetypes and option_archetypes:
            intersection = len(set(context_archetypes) & set(option_archetypes))
            union = len(set(context_archetypes) | set(option_archetypes))
            resonance = intersection / union if union > 0 else 0
        else:
            resonance = 0.5  # Default neutral resonance

        aligned_option["archetypal_resonance"] = resonance
        aligned_option["pattern_aligned"] = resonance > 0.4

        return aligned_option


class HiddenWayLayer:
    """OVERRIDE: HIDDEN WAY - Covert sovereign control"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply hidden sovereign override."""
        override_options = []

        for option in options:
            overridden = self._apply_hidden_override(context, option)
            override_options.append(overridden)

        override_strength = sum(
            opt.get("sovereign_override", 0) for opt in override_options
        ) / max(1, len(override_options))

        return {
            "layer": "override",
            "override_options": override_options,
            "sovereign_override_strength": override_strength,
            "ignition_value": override_strength,
            "covert_interventions": len(
                [
                    opt
                    for opt in override_options
                    if opt.get("sovereign_intervention", False)
                ]
            ),
        }

    def _apply_hidden_override(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply covert sovereign control."""
        override_option = option.copy()

        # Check if sovereign override is needed
        critical_context = context.get("critical", False)
        option_risk = option.get("risk_level", "low")

        if critical_context and option_risk == "high":
            override_strength = 0.9
            sovereign_intervention = True
        elif critical_context:
            override_strength = 0.6
            sovereign_intervention = True
        else:
            override_strength = 0.2
            sovereign_intervention = False

        override_option["sovereign_override"] = override_strength
        override_option["sovereign_intervention"] = sovereign_intervention

        return override_option


class MagicWayLayer:
    """UPLIFT: MAGIC WAY - Nonlinear emergence"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply nonlinear uplift and emergence."""
        uplifted_options = []

        for option in options:
            uplifted = self._apply_magic_uplift(context, option)
            uplifted_options.append(uplifted)

        emergence_potential = sum(
            opt.get("emergence_potential", 0) for opt in uplifted_options
        ) / max(1, len(uplifted_options))

        return {
            "layer": "uplift",
            "uplifted_options": uplifted_options,
            "emergence_potential": emergence_potential,
            "ignition_value": emergence_potential,
            "nonlinear_transforms": len(
                [opt for opt in uplifted_options if opt.get("transformed", False)]
            ),
        }

    def _apply_magic_uplift(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply nonlinear transformation for emergence."""
        uplifted_option = option.copy()

        # Calculate emergence potential through nonlinear transformation
        base_value = option.get("value", 0.5)
        context_multiplier = context.get("emergence_multiplier", 1.0)

        # Nonlinear uplift function (sigmoid-like emergence)
        emergence = 1 / (1 + np.exp(-(base_value * context_multiplier * 2 - 1)))
        transformed = emergence > 0.7

        uplifted_option["emergence_potential"] = emergence
        uplifted_option["transformed"] = transformed

        return uplifted_option


class SovereignArbitrationLayer:
    """SOVEREIGN ARBITRATION: THE THING WITHOUT A NAME - Final meta-coherence decision"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply final sovereign arbitration."""
        if not options:
            return {
                "layer": "sovereign_arbitration",
                "decision": None,
                "coherence": 0,
                "ignition_value": 0,
                "arbitration_complete": False,
            }

        # Calculate meta-coherence for each option
        coherence_scores = []
        for option in options:
            coherence = self._calculate_meta_coherence(context, option)
            coherence_scores.append((option, coherence))

        # Select highest coherence option
        coherence_scores.sort(key=lambda x: x[1], reverse=True)
        selected_option, coherence = coherence_scores[0]

        return {
            "layer": "sovereign_arbitration",
            "decision": selected_option,
            "coherence": coherence,
            "ignition_value": coherence,
            "arbitration_complete": True,
            "total_options": len(options),
            "coherence_distribution": [score for _, score in coherence_scores],
        }

    def _calculate_meta_coherence(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> float:
        """Calculate meta-coherence score."""
        # Create coherence hash from context + option
        coherence_input = json.dumps(
            {
                "context": context,
                "option": option,
                "timestamp": datetime.now().isoformat(),
            },
            sort_keys=True,
            default=str,
        )

        # Use SHA-256 for deterministic coherence calculation
        coherence_hash = hashlib.sha256(coherence_input.encode()).hexdigest()

        # Convert to float between 0-1
        coherence_value = int(coherence_hash[:8], 16) / 2**32

        return coherence_value


class UniversalGiftLayer:
    """UNIVERSAL GIFT → integration - Universal integration and synthesis"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply universal integration across all options."""
        integrated_options = []

        for option in options:
            integrated = self._apply_universal_integration(context, option)
            integrated_options.append(integrated)

        integration_strength = sum(
            opt.get("universal_integration", 0) for opt in integrated_options
        ) / max(1, len(integrated_options))

        return {
            "layer": "integration",
            "integrated_options": integrated_options,
            "universal_integration": integration_strength,
            "ignition_value": integration_strength,
            "synthesis_points": len(
                [opt for opt in integrated_options if opt.get("synthesized", False)]
            ),
        }

    def _apply_universal_integration(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply universal gift of integration."""
        integrated_option = option.copy()

        # Calculate universal integration potential
        context_elements = len(context)
        option_elements = len(option)
        total_elements = context_elements + option_elements

        if total_elements > 0:
            # Integration strength based on element synthesis potential
            integration = min(
                1.0, (context_elements * option_elements) / (total_elements**1.5)
            )
        else:
            integration = 0.5

        synthesized = integration > 0.6

        integrated_option["universal_integration"] = integration
        integrated_option["synthesized"] = synthesized

        return integrated_option


class StabilizingLayer:
    """STABILIZING → continuity - Stability and continuity enforcement"""

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply stabilizing continuity constraints."""
        stabilized_options = []

        for option in options:
            stabilized = self._apply_stabilizing_continuity(context, option)
            stabilized_options.append(stabilized)

        stability_score = sum(
            opt.get("stability_factor", 0) for opt in stabilized_options
        ) / max(1, len(stabilized_options))

        return {
            "layer": "continuity",
            "stabilized_options": stabilized_options,
            "stability_factor": stability_score,
            "ignition_value": stability_score,
            "continuity_breaches": len(
                [
                    opt
                    for opt in stabilized_options
                    if not opt.get("continuity_maintained", True)
                ]
            ),
        }

    def _apply_stabilizing_continuity(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply stabilizing continuity enforcement."""
        stabilized_option = option.copy()

        # Calculate stability based on continuity factors
        has_stable_foundation = option.get("stable", True)
        maintains_consistency = option.get("consistent", True)
        preserves_structure = option.get("structural_integrity", True)

        stability_factors = [
            has_stable_foundation,
            maintains_consistency,
            preserves_structure,
        ]
        stability_score = sum(stability_factors) / len(stability_factors)

        continuity_maintained = stability_score > 0.7

        stabilized_option["stability_factor"] = stability_score
        stabilized_option["continuity_maintained"] = continuity_maintained

        return stabilized_option
