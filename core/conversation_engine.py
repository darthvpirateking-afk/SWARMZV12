"""NEXUSMON Conversation Engine

Core orchestrator for conversational AI in SWARMZ.
Combines intent classification, mode selection, and response generation
with strict adherence to operator sovereignty invariants.
"""

from typing import List, Optional, Tuple
from collections import defaultdict

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


class IntentClassifier:
    """Classifies user intent from messages."""

    # Intent patterns (simple keyword-based for now)
    INTENT_PATTERNS = {
        "stuck": ["stuck", "blocked", "can't", "struggling", "confused"],
        "help_plan": ["help me plan", "plan", "how do i", "what should i", "design"],
        "explain": ["why", "how does", "explain", "what is", "what does"],
        "status": [
            "what is happening",
            "status",
            "what are you doing",
            "current state",
        ],
        "reflect": ["how am i", "patterns", "what do i", "am i"],
        "mission": ["mission", "task", "goal", "create"],
    }

    @staticmethod
    def classify(message: str) -> str:
        """Classify intent from user message.

        Args:
            message: User message text

        Returns:
            Intent string (e.g., "stuck", "help_plan", etc.)
        """
        msg_lower = message.lower()
        intents_found = defaultdict(int)

        for intent, keywords in IntentClassifier.INTENT_PATTERNS.items():
            for keyword in keywords:
                if keyword in msg_lower:
                    intents_found[intent] += 1

        if not intents_found:
            return "general"

        # Return intent with highest score
        return max(intents_found, key=intents_found.get)


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
3. Ask clarifying questions
4. Never prescribe; only reflect
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        # For now, generate a reflection reply (in production, call LLM)
        reply = self._generate_stub_reply(message, "Reflect", context)

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
1. Ask about the goal
2. Identify constraints
3. Suggest structure
4. Build mission_draft payload
"""
        prompt = system_prompt + "\n\n" + mode_guidance

        reply = self._generate_stub_reply(message, "Plan", context)

        # Create a stub mission draft
        mission_draft = MissionDraft(
            situation={"inferred": "from conversation"},
            goal="To be refined with operator",
            constraints={},
            evidence={},
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

        reply = self._generate_stub_reply(message, "Explain", context)

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

        reply = self._generate_stub_reply(message, "Nudge", context)

        return reply, [], None

    def _handle_mission_draft(
        self,
        message: str,
        persona: Persona,
        context: ConversationContext,
        context_summary: str,
    ) -> Tuple[str, List[SuggestedAction], Optional[MissionDraft]]:
        """Handle MISSION_DRAFT mode: formalize chat into mission."""
        reply = "I've extracted a mission draft from our conversation. Review it below, then create the mission."

        mission_draft = MissionDraft(
            situation={"from_conversation": message[:200]},
            goal="Extract from conversation",
            constraints={"inferred": "from context"},
            evidence={},
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

    def _generate_stub_reply(
        self, message: str, mode: str, context: ConversationContext
    ) -> str:
        """Generate a stub reply for demonstration.

        In production, this would call the LLM with the system prompt.
        """
        return f'[{mode}] I hear you saying: "{message[:50]}..." Let me respond in this way...'

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
