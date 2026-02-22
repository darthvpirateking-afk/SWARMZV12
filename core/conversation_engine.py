"""NEXUSMON Conversation Engine

Core orchestrator for conversational AI in SWARMZ.
Combines intent classification, mode selection, and response generation
with strict adherence to operator sovereignty invariants.
"""

from typing import List, Optional, Tuple
import os
import json

from core.nexusmon_models import (
    ConversationContext,
    ChatReply,
    ChatModeType,
    SuggestedAction,
    SuggestedActionType,
    MissionDraft,
    StateSnapshot,
    Persona,
)
from core.persona_engine import get_persona, get_system_prompt
from core.memory_engine import get_memory_engine
from core.model_router import call as model_call, is_offline, get_model_config
from operator_interface.commands import nudge_operator


class IntentClassifier:
    """Classifies user intent from messages."""

    VALID_INTENTS = {
        "stuck",
        "help_plan",
        "explain",
        "status",
        "reflect",
        "mission",
        "general",
    }

    @staticmethod
    def _has_model_key() -> bool:
        cfg = get_model_config()
        provider = cfg.get("provider", "anthropic")
        provider_cfg = cfg.get(provider, {})
        key_env = provider_cfg.get("apiKeyEnv", "")
        return bool(os.environ.get(key_env)) if key_env else False

    @staticmethod
    def classify(message: str) -> str:
        """Classify intent from user message.

        Args:
            message: User message text

        Returns:
            Intent string (e.g., "stuck", "help_plan", etc.)
        """
        if is_offline() or not IntentClassifier._has_model_key():
            return "general"

        system = (
            "You classify operator intent for NEXUSMON. "
            "Return exactly one token from: "
            "stuck, help_plan, explain, status, reflect, mission, general. "
            "No punctuation, no explanation."
        )
        result = model_call(
            [{"role": "user", "content": message}],
            system=system,
            max_tokens=8,
        )
        if not result.get("ok"):
            return "general"

        intent = (result.get("text") or "").strip().lower()
        return intent if intent in IntentClassifier.VALID_INTENTS else "general"


class ModeSelector:
    """Selects response mode based on intent and context."""

    @staticmethod
    def select_mode(intent: str, context: ConversationContext) -> ChatModeType:
        """Select appropriate response mode.

        Args:
            intent: Classified user intent
            context: Full conversation context

        Returns:
            ChatModeType (Reflect, Plan, Explain, Nudge, MissionDraft, Status)
        """
        # If system is degraded (high entropy), prefer Reflect/Nudge
        if context.health.entropy > 0.7:
            return ChatModeType.REFLECT

        # Intent-based selection
        if intent == "stuck":
            # Stuck = Reflect (patterns) + possible Nudge
            if context.operator.drift_score > 0.6:
                return ChatModeType.NUDGE
            return ChatModeType.REFLECT

        elif intent == "help_plan":
            return ChatModeType.PLAN

        elif intent == "explain":
            return ChatModeType.EXPLAIN

        elif intent == "status":
            return ChatModeType.STATUS

        elif intent == "mission":
            return ChatModeType.MISSION_DRAFT

        else:  # general
            # Default to Reflect if confused
            return ChatModeType.REFLECT


class ConversationEngine:
    """Main conversational logic orchestrator."""

    def __init__(self):
        """Initialize conversation engine."""
        self.intent_classifier = IntentClassifier()
        self.mode_selector = ModeSelector()
        self.memory_engine = get_memory_engine()

    def generate_reply(self, message: str, context: ConversationContext) -> ChatReply:
        """Generate a conversational reply.

        Args:
            message: User message
            context: Full conversation context

        Returns:
            ChatReply with reply text, mode, suggested actions, etc.
        """
        # 1. Classify intent
        intent = self.intent_classifier.classify(message)

        # 2. Select mode
        mode = self.mode_selector.select_mode(intent, context)

        # 3. Get persona
        persona = get_persona(context.operator, context.nexus_form)
        context.persona = persona

        # 4. Build context summary for LLM
        context_summary = self._build_context_summary(context, intent)

        # 5. Route to specific handler based on mode
        reply_text, suggested_actions, mission_draft = self._route(
            message=message,
            mode=mode,
            persona=persona,
            context=context,
            context_summary=context_summary,
        )

        # 6. Build state snapshot
        snapshot = self._build_state_snapshot(context)

        return ChatReply(
            reply=reply_text,
            mode=mode,
            suggested_actions=suggested_actions,
            mission_draft=mission_draft,
            state_snapshot=snapshot,
        )

    def _build_context_summary(self, context: ConversationContext, intent: str) -> str:
        """Build a concise context summary for the LLM prompt.

        Args:
            context: Conversation context
            intent: Classified intent

        Returns:
            Context summary string
        """
        parts = []

        # Recent conversation
        if context.history:
            recent_turns_summary = self.memory_engine.summarize_turns(
                context.history[-5:]
            )
            parts.append(f"Recent conversation: {recent_turns_summary}")

        # Operator state
        if context.operator:
            parts.append(
                f"Operator state: risk={context.operator.risk_posture}, "
                f"drift={context.operator.drift_score:.2f}, "
                f"fatigue={context.operator.fatigue:.2f}"
            )

        # NexusForm
        if context.nexus_form:
            parts.append(
                f"Evolution: currently in {context.nexus_form.current_form.value} form"
            )

        # Active missions
        if context.missions:
            active = [m for m in context.missions if m.get("status") == "RUNNING"]
            if active:
                parts.append(f"Active missions: {len(active)}")

        # Health
        if context.health:
            parts.append(
                f"System health: entropy={context.health.entropy:.2f}, "
                f"drift={context.health.drift:.2f}, "
                f"coherence={context.health.coherence:.2f}"
            )

        # Current intent
        parts.append(f"User intent: {intent}")

        return " | ".join(parts)

    def _route(
        self,
        message: str,
        mode: ChatModeType,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Route to specific mode handler.

        Args:
            message: User message
            mode: Selected response mode
            persona: Selected persona
            context: Conversation context
            context_summary: Context summary for LLM

        Returns:
            Tuple of (reply_text, suggested_actions, mission_draft)
        """
        if mode == ChatModeType.REFLECT:
            return self._handle_reflect(message, persona, context, context_summary)
        elif mode == ChatModeType.PLAN:
            return self._handle_plan(message, persona, context, context_summary)
        elif mode == ChatModeType.EXPLAIN:
            return self._handle_explain(message, persona, context, context_summary)
        elif mode == ChatModeType.NUDGE:
            return self._handle_nudge(message, persona, context, context_summary)
        elif mode == ChatModeType.MISSION_DRAFT:
            return self._handle_mission_draft(
                message, persona, context, context_summary
            )
        elif mode == ChatModeType.STATUS:
            return self._handle_status(message, persona, context, context_summary)
        else:
            # Fallback
            return self._handle_reflect(message, persona, context, context_summary)

    def _handle_reflect(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle REFLECT mode: mirror patterns and friction."""
        system_prompt = get_system_prompt(persona, context_summary)
        mode_guidance = """
Mode: REFLECT
Objective: Mirror back patterns, friction, and drift you observe.
Tone: Curious, non-judgmental, pattern-seeking.

Tasks:
1. Acknowledge what you hear
2. Name a pattern or friction you've observed
3. If context is incomplete, state your assumptions briefly and continue
4. Never prescribe; only reflect
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        reply = self._generate_ai_reply(
            message=message,
            mode="Reflect",
            system_prompt=system_prompt,
            mode_guidance=mode_guidance,
            context=context,
        )

        suggested_actions = []
        if context.health.entropy > 0.6:
            suggested_actions.append(
                SuggestedAction(
                    type=SuggestedActionType.VIEW_METRICS, payload={"screen": "Metrics"}
                )
            )

        return reply, suggested_actions, None

    def _handle_plan(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle PLAN mode: co-structure missions."""
        system_prompt = get_system_prompt(persona, context_summary)
        mode_guidance = """
Mode: PLAN
Objective: Co-structure a mission with the operator.
Tone: Collaborative, structural, concrete.

Tasks:
1. Infer goal and constraints from available context
2. If context is incomplete, state assumptions in one line and proceed
3. Suggest a concrete structure with prioritized steps
4. Build mission_draft payload without asking follow-up questions
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        # Create a mission draft artifact
        mission_draft = MissionDraft(
            situation={"from_message": message[:200], "inferred": "from context"},
            goal="Operator-requested modification plan",
            constraints={"inferred": "from context"},
            evidence={"intent": "help_plan"},
        )

        ai_reply = self._generate_ai_reply(
            message=message,
            mode="Plan",
            system_prompt=system_prompt,
            mode_guidance=mode_guidance,
            context=context,
        )

        apply_requested = self._is_apply_requested(message)
        reply = self._build_artifact_reply(
            mode="Plan",
            ai_body=ai_reply,
            artifact=mission_draft.model_dump(),
            works="yes",
            applied="yes" if apply_requested else "no",
            what_else=[
                "Review artifact details and constraints",
                "Run targeted validation for affected component",
                "Promote artifact into an executable mission",
            ],
        )

        suggested_actions = [
            SuggestedAction(
                type=SuggestedActionType.CREATE_MISSION,
                payload=mission_draft.model_dump(),
            )
        ]

        return reply, suggested_actions, mission_draft

    def _handle_explain(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle EXPLAIN mode: clarify system state and concepts."""
        system_prompt = get_system_prompt(persona, context_summary)
        mode_guidance = """
Mode: EXPLAIN
Objective: Clarify system state, screens, and mechanisms.
Tone: Teaching-oriented, clear, concrete.

Tasks:
1. Identify what's being asked
2. Explain with examples if possible
3. Ground in audit trails or visible state
4. Avoid jargon unless operator knows it
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        reply = self._generate_ai_reply(
            message=message,
            mode="Explain",
            system_prompt=system_prompt,
            mode_guidance=mode_guidance,
            context=context,
        )

        suggested_actions = [
            SuggestedAction(
                type=SuggestedActionType.VIEW_AUDIT, payload={"screen": "Audit"}
            )
        ]

        return reply, suggested_actions, None

    def _handle_nudge(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle NUDGE mode: gentle structural suggestions."""
        system_prompt = get_system_prompt(persona, context_summary)
        mode_guidance = """
Mode: NUDGE
Objective: Offer gentle, structural suggestions.
Tone: Respectful, non-prescriptive, pattern-aware.

Constraints:
- NEVER emotional manipulation
- NEVER autonomy override
- Always frame as observation + suggestion
- Always honor operator choice

Tasks:
1. Name the pattern you observe
2. Suggest an alternative approach
3. Explain the reasoning
4. Respect their decision if they decline
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        reply = self._generate_ai_reply(
            message=message,
            mode="Nudge",
            system_prompt=system_prompt,
            mode_guidance=mode_guidance,
            context=context,
        )
        nudge_artifact = nudge_operator(
            message=reply,
            state_snapshot=self._build_state_snapshot(context).model_dump(mode="json"),
            intent="nudge",
        )

        response = self._build_artifact_reply(
            mode="Nudge",
            ai_body=reply,
            artifact=nudge_artifact,
            works="yes",
            applied="no",
            what_else=[
                "Review justification before acting",
                "Confirm action aligns with current mission",
                "Apply manually if approved",
            ],
        )

        return response, [], None

    def _handle_mission_draft(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle MISSION_DRAFT mode: formalize chat into mission."""
        mission_draft = MissionDraft(
            situation={"from_conversation": message[:200]},
            goal="Extract from conversation",
            constraints={"inferred": "from context"},
            evidence={},
        )

        apply_requested = self._is_apply_requested(message)
        ai_reply = self._generate_ai_reply(
            message=message,
            mode="MissionDraft",
            system_prompt=get_system_prompt(persona, context_summary),
            mode_guidance=(
                "Mode: MISSION_DRAFT\n"
                "Objective: Produce a concrete artifact and execution framing.\n"
                "Return concise, implementation-ready content."
            ),
            context=context,
        )
        reply = self._build_artifact_reply(
            mode="MissionDraft",
            ai_body=ai_reply,
            artifact=mission_draft.model_dump(),
            works="yes",
            applied="yes" if apply_requested else "no",
            what_else=[
                "Confirm operator approval boundary",
                "Execute prepared action in mission pipeline",
                "Record outcome in audit trail",
            ],
        )

        suggested_actions = [
            SuggestedAction(
                type=SuggestedActionType.CREATE_MISSION,
                payload=mission_draft.model_dump(),
            )
        ]

        return reply, suggested_actions, mission_draft

    def _handle_status(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle STATUS mode: summarize current state."""
        parts = []

        if context.missions:
            running = [m for m in context.missions if m.get("status") == "RUNNING"]
            parts.append(f"Running: {len(running)} missions")

        if context.health:
            parts.append(
                f"Health: entropy {context.health.entropy:.1%}, "
                f"coherence {context.health.coherence:.1%}"
            )

        if context.nexus_form:
            parts.append(f"Form: {context.nexus_form.current_form.value}")

        reply = "Current state: " + " | ".join(parts)

        suggested_actions = [
            SuggestedAction(
                type=SuggestedActionType.VIEW_METRICS, payload={"screen": "Metrics"}
            )
        ]

        return reply, suggested_actions, None

    def _generate_ai_reply(
        self,
        message: str,
        mode: str,
        system_prompt: str,
        mode_guidance: str,
        context: ConversationContext,
    ) -> str:
        """Generate a reply via model_router with minimal deterministic fallback."""
        if is_offline() or not IntentClassifier._has_model_key():
            return (
                f"[{mode}] Offline/no-key fallback: I understand your request and can help, "
                "but live model responses are unavailable right now."
            )

        full_system = system_prompt + "\n\n" + mode_guidance
        result = model_call(
            [{"role": "user", "content": message}],
            system=full_system,
            max_tokens=450,
        )
        if result.get("ok") and result.get("text"):
            return result["text"].strip()

        err = (result.get("error") or "unknown").strip()
        return (
            f"[{mode}] Model call failed ({err[:120]}). "
            "Please retry or check model/API-key configuration."
        )

    def _is_apply_requested(self, message: str) -> bool:
        """Return True when operator explicitly asks to apply/execute."""
        lowered = message.lower()
        tokens = ("apply", "execute", "run it", "ship it", "do it now")
        return any(token in lowered for token in tokens)

    def _build_artifact_reply(
        self,
        mode: str,
        ai_body: str,
        artifact: dict,
        works: str,
        applied: str,
        what_else: List[str],
    ) -> str:
        """Build a consistent, explicit artifact response contract."""
        artifact_json = json.dumps(artifact, ensure_ascii=False)
        next_steps = "\n".join(f"- {item}" for item in what_else)
        return (
            f"[{mode}]\n"
            f"artifact:\n{artifact_json}\n\n"
            f"works: {works}\n"
            f"applied: {applied}\n"
            f"what_else:\n{next_steps}\n\n"
            f"analysis:\n{ai_body}"
        )

    def _build_state_snapshot(self, context: ConversationContext) -> StateSnapshot:
        """Build state snapshot for response."""
        return StateSnapshot(
            nexus_form=context.nexus_form.current_form if context.nexus_form else None,
            system_health=context.health,
            active_missions=len(
                [m for m in context.missions if m.get("status") == "RUNNING"]
            ),
        )


# Global instance
_conversation_engine: Optional[ConversationEngine] = None


def get_conversation_engine() -> ConversationEngine:
    """Get or create the global conversation engine."""
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = ConversationEngine()
    return _conversation_engine
