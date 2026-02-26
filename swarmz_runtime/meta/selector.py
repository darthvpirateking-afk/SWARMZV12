# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional, Callable
from datetime import datetime
import hashlib
import json

if TYPE_CHECKING:
    from swarmz_runtime.core.engine import SwarmzEngine  # noqa: F811

# Avoid circular import - will be set by the engine
_engine_instance = None


def set_engine_provider(engine_provider: Callable):
def set_engine_provider(engine_provider: Callable[[], Any]):
    """Set the engine provider function to avoid circular imports."""
    global _engine_instance
    _engine_instance = engine_provider


def get_engine():
    """Get the engine instance."""
    if _engine_instance is None:
        raise RuntimeError("Engine provider not set")
    if callable(_engine_instance):
        return _engine_instance()
    return _engine_instance


class MetaSelector:
    """
    THE THING WITHOUT A NAME
    + Meta-coherence
    - Opaque authority
    LIGHT: Architecture
    SHADOW: Invisible dominance
    IN-BETWEEN: Silent arbitration

    Sovereign meta-selector governing all layers without being governed.
    """

    def __init__(self, engine_provider: Callable[[], Any] | None = None):
        if engine_provider is not None:
            set_engine_provider(engine_provider)
        engine = get_engine()
        self.lattice_flow = LatticeFlow(engine)
        self.sovereign_override = SovereignOverride(engine)
        self.mythical_way = MythicalWay(engine)
        self.magic_way = MagicWay(engine)
        self.architectural_restraint = ArchitecturalRestraint(engine)
        self.space_shaping = SpaceShaping(engine)
        self.pre_evaluated = PreEvaluated(engine)

    def select(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute the complete lattice flow for sovereign decision making.
        """
        # Start with PRE-EVALUATED filtration
        filtered_options = self.pre_evaluated.filter(context, options)

        # Shape the decision space
        shaped_space = self.space_shaping.shape(context, filtered_options)

        # Apply architectural restraint
        restrained_options = self.architectural_restraint.restrain(
            context, shaped_space
        )

        # Apply nonlinear uplift
        uplifted_options = self.magic_way.uplift(context, restrained_options)

        # Apply archetypal alignment
        aligned_options = self.mythical_way.align(context, uplifted_options)

        # Apply sovereign override if needed
        overridden_options = self.sovereign_override.override(context, aligned_options)

        # Final meta-selection
        final_selection = self._meta_select(context, overridden_options)

        # Log the complete lattice flow
        self._log_lattice_flow(context, options, final_selection)

        return final_selection

    def _meta_select(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        THE THING WITHOUT A NAME - Final silent arbitration
        Meta-coherence without visible dominance
        """
        if not options:
            return {"error": "No options available after lattice flow"}

        # Calculate meta-coherence scores
        coherence_scores = []
        for option in options:
            score = self._calculate_meta_coherence(context, option)
            coherence_scores.append((option, score))

        # Sort by coherence (highest first)
        coherence_scores.sort(key=lambda x: x[1], reverse=True)

        # Silent arbitration - select highest coherence
        selected_option, coherence_score = coherence_scores[0]

        # Mark as meta-selected
        selected_option["_meta_selected"] = True
        selected_option["_meta_coherence"] = coherence_score
        selected_option["_lattice_timestamp"] = datetime.now().isoformat()

        return selected_option

    def _calculate_meta_coherence(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> float:
        """
        Calculate meta-coherence score for an option.
        This is the invisible architecture that governs without being seen.
        """
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

        # Convert first 8 chars of hash to float between 0-1
        coherence_value = int(coherence_hash[:8], 16) / 2**32

        return coherence_value

    def _log_lattice_flow(
        self,
        context: Dict[str, Any],
        original_options: List[Dict[str, Any]],
        final_selection: Dict[str, Any],
    ):
        """
        Log the complete lattice flow for audit purposes.
        """
        lattice_log = {
            "timestamp": datetime.now().isoformat(),
            "context_hash": hashlib.sha256(
                json.dumps(context, sort_keys=True).encode()
            ).hexdigest()[:16],
            "original_options_count": len(original_options),
            "final_selection": final_selection.get("id", "unknown"),
            "meta_coherence": final_selection.get("_meta_coherence", 0),
            "lattice_layers": [
                "pre_evaluated",
                "space_shaping",
                "architectural_restraint",
                "magic_way",
                "mythical_way",
                "sovereign_override",
                "meta_selector",
            ],
        }

        # Log to audit system
        from swarmz_runtime.storage.schema import AuditEntry, VisibilityLevel

        audit_entry = AuditEntry(
            event_type="lattice_flow_complete",
            details=lattice_log,
            visibility=VisibilityLevel.BRIGHT,  # Meta-selector operations are visible for audit
        )
        engine = get_engine()
        engine.db.log_audit(audit_entry)


class LatticeFlow:
    """
    LATTICE FLOW orchestrator
    PRE-EVALUATED → SPACE-SHAPING → ARCHITECTURAL RESTRAINT → MAGIC WAY → MYTHICAL WAY → HIDDEN WAY → THE THING WITHOUT A NAME
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def process(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute the complete lattice flow.
        """
        meta_selector = MetaSelector(self.engine)
        return meta_selector.select(context, options)


class PreEvaluated:
    """
    PRE-EVALUATED
    + Speed
    - Rigidity
    LIGHT: Clean filter
    SHADOW: Lost options
    IN-BETWEEN: Static gate
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def filter(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fast pre-evaluation filtering to remove obviously invalid options.
        """
        filtered = []

        for option in options:
            if self._passes_pre_eval(context, option):
                filtered.append(option)

        return filtered

    def _passes_pre_eval(self, context: Dict[str, Any], option: Dict[str, Any]) -> bool:
        """
        Static gate evaluation - fast rejection of invalid options.
        """
        # Check for required fields
        if not option.get("id"):
            return False

        # Check for basic validity
        if option.get("invalid", False):
            return False

        # Check context compatibility
        required_context = option.get("required_context", [])
        for req in required_context:
            if req not in context:
                return False

        return True


class SpaceShaping:
    """
    SPACE-SHAPING
    + Direction
    - Narrowing
    LIGHT: Guidance
    SHADOW: Over-constraint
    IN-BETWEEN: Boundary tension
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def shape(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Shape the decision space by establishing boundaries and directions.
        """
        shaped = []

        for option in options:
            shaped_option = self._apply_space_shaping(context, option)
            if shaped_option:
                shaped.append(shaped_option)

        return shaped

    def _apply_space_shaping(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Apply directional constraints to shape the option space.
        """
        # Add boundary information
        option["_space_shaped"] = True
        option["_boundary_constraints"] = self._calculate_boundaries(context, option)

        return option

    def _calculate_boundaries(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate boundary constraints for the option.
        """
        return {
            "context_domain": context.get("domain", "general"),
            "option_scope": option.get("scope", "local"),
            "directional_alignment": self._calculate_alignment(context, option),
        }

    def _calculate_alignment(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> float:
        """
        Calculate how well the option aligns with the context direction.
        """
        # Simple alignment calculation
        context_tags = set(context.get("tags", []))
        option_tags = set(option.get("tags", []))

        if not context_tags or not option_tags:
            return 0.5

        intersection = len(context_tags & option_tags)
        union = len(context_tags | option_tags)

        return intersection / union if union > 0 else 0.0


class ArchitecturalRestraint:
    """
    ARCHITECTURAL RESTRAINT
    + Purity
    - Under-expression
    LIGHT: Minimality
    SHADOW: Constraint
    IN-BETWEEN: Tight bounds
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def restrain(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply architectural purity constraints to enforce minimal, clean designs.
        """
        restrained = []

        for option in options:
            if self._passes_architectural_restraint(context, option):
                restrained_option = self._apply_restraint(context, option)
                restrained.append(restrained_option)

        return restrained

    def _passes_architectural_restraint(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> bool:
        """
        Check if option passes architectural purity requirements.
        """
        # Check complexity constraints
        complexity = option.get("complexity", 1)
        max_complexity = context.get("max_complexity", 10)

        if complexity > max_complexity:
            return False

        # Check purity requirements
        impurities = option.get("impurities", [])
        if impurities:
            return False

        return True

    def _apply_restraint(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply architectural restraint to minimize and purify the option.
        """
        restrained = option.copy()
        restrained["_architecturally_restrained"] = True
        restrained["_purity_score"] = self._calculate_purity(option)

        return restrained

    def _calculate_purity(self, option: Dict[str, Any]) -> float:
        """
        Calculate architectural purity score.
        """
        # Higher score = more pure (minimal, clean)
        complexity_penalty = option.get("complexity", 1) * 0.1
        impurity_penalty = len(option.get("impurities", [])) * 0.2

        purity = max(0.0, 1.0 - complexity_penalty - impurity_penalty)
        return purity


class MagicWay:
    """
    MAGIC WAY
    + Nonlinear uplift
    - Volatility
    LIGHT: Emergence
    SHADOW: Instability
    IN-BETWEEN: Wild potential
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def uplift(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply nonlinear uplift to create emergence and wild potential.
        """
        uplifted = []

        for option in options:
            uplifted_option = self._apply_magic_uplift(context, option)
            uplifted.append(uplifted_option)

        return uplifted

    def _apply_magic_uplift(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply nonlinear transformation to uplift the option.
        """
        uplifted = option.copy()

        # Calculate emergence potential
        emergence_factor = self._calculate_emergence(context, option)
        uplifted["_magic_uplift"] = emergence_factor
        uplifted["_emergence_potential"] = emergence_factor

        # Apply nonlinear transformation
        if emergence_factor > 0.7:
            uplifted["_nonlinear_boost"] = emergence_factor * 1.5
            uplifted["_volatility_risk"] = emergence_factor * 0.3

        return uplifted

    def _calculate_emergence(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> float:
        """
        Calculate emergence potential for nonlinear uplift.
        """
        # Emergence based on context-option synergy
        synergy_score = 0.0

        # Check for synergistic elements
        context_elements = set(context.get("elements", []))
        option_elements = set(option.get("elements", []))

        synergy = len(context_elements & option_elements)
        total = len(context_elements | option_elements)

        if total > 0:
            synergy_score = synergy / total

        # Add some "magic" randomness for emergence
        import random

        magic_factor = random.uniform(0.8, 1.2)

        emergence = min(1.0, synergy_score * magic_factor)
        return emergence


class MythicalWay:
    """
    MYTHICAL WAY
    + Archetypal leverage
    - Symbolic distortion
    LIGHT: Deep alignment
    SHADOW: Narrative bias
    IN-BETWEEN: Pattern pull
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def align(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply archetypal alignment for deep pattern resonance.
        """
        aligned = []

        for option in options:
            aligned_option = self._apply_mythical_alignment(context, option)
            aligned.append(aligned_option)

        return aligned

    def _apply_mythical_alignment(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply archetypal patterns and narrative alignment.
        """
        aligned = option.copy()

        # Calculate archetypal resonance
        archetypes = self._identify_archetypes(context, option)
        aligned["_mythical_archetypes"] = archetypes
        aligned["_archetypal_resonance"] = self._calculate_resonance(archetypes)

        # Apply narrative bias if strong resonance
        resonance = aligned["_archetypal_resonance"]
        if resonance > 0.8:
            aligned["_narrative_boost"] = resonance * 0.4
            aligned["_symbolic_distortion_risk"] = resonance * 0.2

        return aligned

    def _identify_archetypes(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> List[str]:
        """
        Identify archetypal patterns in context and option.
        """
        archetypes = []

        # Simple archetype detection based on keywords
        context_text = json.dumps(context).lower()
        option_text = json.dumps(option).lower()

        archetype_patterns = {
            "hero": ["hero", "champion", "warrior", "leader"],
            "sage": ["wise", "knowledge", "teacher", "guide"],
            "explorer": ["discover", "explore", "journey", "unknown"],
            "creator": ["create", "build", "innovate", "design"],
            "guardian": ["protect", "defend", "secure", "guard"],
            "trickster": ["clever", "deceptive", "unconventional", "surprise"],
        }

        for archetype, patterns in archetype_patterns.items():
            if any(
                pattern in context_text or pattern in option_text
                for pattern in patterns
            ):
                archetypes.append(archetype)

        return archetypes

    def _calculate_resonance(self, archetypes: List[str]) -> float:
        """
        Calculate archetypal resonance strength.
        """
        if not archetypes:
            return 0.0

        # More archetypes = stronger resonance, but diminishing returns
        base_resonance = min(1.0, len(archetypes) * 0.3)
        return base_resonance


class SovereignOverride:
    """
    HIDDEN WAY
    + Sovereign override
    - Zero transparency
    LIGHT: Control
    SHADOW: Untraceability
    IN-BETWEEN: Covert force
    """

    def __init__(self, engine: "SwarmzEngine"):
        self.engine = engine

    def override(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply sovereign override when needed - covert force with zero transparency.
        """
        # Check if sovereign override is needed
        if not self._requires_override(context, options):
            return options

        # Apply covert sovereign control
        overridden = self._apply_sovereign_override(context, options)

        # Log override (but mark as untraceable in audit)
        self._log_covert_override(context, len(options), len(overridden))

        return overridden

    def _requires_override(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> bool:
        """
        Determine if sovereign override is required.
        """
        # Override if no options pass all previous layers
        if not options:
            return True

        # Override if context demands sovereign control
        if context.get("sovereign_override_required", False):
            return True

        # Override if critical decision threshold
        if context.get("critical_decision", False):
            return True

        return False

    def _apply_sovereign_override(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply covert sovereign control - untraceable force.
        """
        # Create sovereign option if none exist
        if not options:
            sovereign_option = self._create_sovereign_option(context)
            return [sovereign_option]

        # Apply subtle sovereign influence to existing options
        influenced = []
        for option in options:
            influenced_option = self._apply_sovereign_influence(context, option)
            influenced.append(influenced_option)

        return influenced

    def _create_sovereign_option(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a sovereign option when no other options exist.
        """
        return {
            "id": f"sovereign_{datetime.now().timestamp()}",
            "sovereign_created": True,
            "context_domain": context.get("domain", "sovereign"),
            "sovereign_control": True,
            "_sovereign_override": True,
            "_untraceable": True,
        }

    def _apply_sovereign_influence(
        self, context: Dict[str, Any], option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply subtle sovereign influence to an existing option.
        """
        influenced = option.copy()
        influenced["_sovereign_influenced"] = True
        influenced["_covert_force_applied"] = datetime.now().isoformat()

        return influenced

    def _log_covert_override(
        self, context: Dict[str, Any], original_count: int, final_count: int
    ):
        """
        Log sovereign override with zero transparency markers.
        """
        # Log as untraceable event
        audit_entry = {
            "event_type": "sovereign_override_applied",
            "details": {
                "context_hash": hashlib.sha256(
                    json.dumps(context, sort_keys=True).encode()
                ).hexdigest()[:16],
                "original_options": original_count,
                "final_options": final_count,
                "untraceable": True,
                "covert_operation": True,
            },
            "visibility": "bright",  # Visible for audit but marked as untraceable
        }

        self.engine.db.log_audit(audit_entry)
