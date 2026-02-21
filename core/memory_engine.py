"""NEXUSMON Memory Engine

Manages both short-term (recent conversation turns) and long-term
(compressed operator memory) for conversational continuity.

All storage is append-only JSONL for audit and safety.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.nexusmon_models import ConversationTurn, OperatorMemory


class MemoryEngine:
    """Manages conversation history and operator memory."""

    def __init__(self, data_dir: Path = Path("data")):
        """Initialize memory engine.

        Args:
            data_dir: Directory for storing JSONL files
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.conversation_turns_file = self.data_dir / "conversation_turns.jsonl"
        self.operator_memory_file = self.data_dir / "operator_memory.jsonl"

        # Ensure files exist
        self.conversation_turns_file.touch(exist_ok=True)
        self.operator_memory_file.touch(exist_ok=True)

    def store_conversation_turn(
        self,
        operator_id: str,
        message: str,
        reply: str,
        mode: str,
        tags: Optional[List[str]] = None,
    ) -> ConversationTurn:
        """Store a single conversation turn.

        Args:
            operator_id: Operator ID
            message: User message
            reply: NEXUSMON reply
            mode: Response mode (Reflect, Plan, etc.)
            tags: Optional tags for categorization

        Returns:
            The stored ConversationTurn
        """
        turn = ConversationTurn(
            id=str(uuid.uuid4()),
            operator_id=operator_id,
            message=message,
            reply=reply,
            mode=mode,
            tags=tags or [],
        )

        # Append to JSONL
        with self.conversation_turns_file.open("a", encoding="utf-8") as f:
            f.write(turn.model_dump_json(by_alias=False) + "\n")

        return turn

    def get_recent_turns(
        self, operator_id: str, limit: int = 20
    ) -> List[ConversationTurn]:
        """Get recent conversation turns for an operator.

        Args:
            operator_id: Operator ID
            limit: Maximum number of turns to return

        Returns:
            List of recent ConversationTurn objects
        """
        if not self.conversation_turns_file.exists():
            return []

        turns = []
        try:
            with self.conversation_turns_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("operator_id") == operator_id:
                            turns.append(ConversationTurn(**obj))
                    except (json.JSONDecodeError, ValueError):
                        pass  # Skip malformed lines
        except OSError:
            return []

        # Return last N turns
        return turns[-limit:] if len(turns) > limit else turns

    def summarize_turns(self, turns: List[ConversationTurn]) -> str:
        """Create a brief summary of conversation turns.

        Args:
            turns: List of conversation turns

        Returns:
            Text summary of patterns and themes
        """
        if not turns:
            return "No prior conversation history."

        # Count modes
        mode_counts: Dict[str, int] = {}
        themes = []
        questions = []

        for turn in turns:
            mode = turn.mode
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

            # Extract questions (simple heuristic)
            if "?" in turn.message:
                questions.append(turn.message[:100])

            # Extract key themes from replies
            if len(turn.reply) > 50:
                themes.append(turn.reply[:80])

        # Build summary
        summary_parts = []

        if mode_counts:
            modes_str = ", ".join(
                f"{mode.value}({count})" for mode, count in sorted(mode_counts.items())
            )
            summary_parts.append(f"Recent modes: {modes_str}")

        if questions:
            summary_parts.append(f"Recent questions: {'; '.join(questions[:3])}")

        if not summary_parts:
            summary_parts.append(f"Recent conversation: {len(turns)} turns")

        return ". ".join(summary_parts)

    def get_operator_memory(self, operator_id: str) -> Optional[OperatorMemory]:
        """Load the current operator memory if it exists.

        Args:
            operator_id: Operator ID

        Returns:
            OperatorMemory if exists, else None
        """
        if not self.operator_memory_file.exists():
            return None

        try:
            with self.operator_memory_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return None

        # Find most recent memory for this operator
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("operator_id") == operator_id:
                    return OperatorMemory(**obj)
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    def update_operator_memory(
        self,
        operator_id: str,
        summary: str,
        tags: Optional[List[str]] = None,
        patterns: Optional[Dict[str, Any]] = None,
    ) -> OperatorMemory:
        """Update long-term operator memory.

        This is called periodically to compress recent turns into
        patterns that inform future responses.

        Args:
            operator_id: Operator ID
            summary: Text summary of learned patterns
            tags: Optional tags
            patterns: Optional dict of learned patterns

        Returns:
            The stored OperatorMemory
        """
        memory = OperatorMemory(
            operator_id=operator_id,
            summary=summary,
            tags=tags or [],
            patterns=patterns or {},
        )

        # Append to JSONL
        with self.operator_memory_file.open("a", encoding="utf-8") as f:
            f.write(memory.model_dump_json(by_alias=False) + "\n")

        return memory

    def extract_patterns(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """Extract operational patterns from conversation turns.

        Args:
            turns: List of conversation turns

        Returns:
            Dictionary of extracted patterns
        """
        if not turns:
            return {}

        patterns = {
            "favorite_modes": {},
            "avoidance_patterns": [],
            "question_themes": [],
            "response_preferences": [],
        }

        # Count mode preferences
        mode_counts: Dict[str, int] = {}
        for turn in turns:
            mode = turn.mode
            if hasattr(mode, "value"):
                mode = mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        patterns["favorite_modes"] = mode_counts

        # Extract themes from longer messages
        for turn in turns:
            msg = turn.message.lower()
            if "avoid" in msg or "don't want" in msg or "skip" in msg:
                patterns["avoidance_patterns"].append(turn.message[:100])
            if "what is" in msg or "why" in msg or "how" in msg:
                patterns["question_themes"].append(turn.message[:100])

        return patterns

    def get_memory_summary_for_context(self, operator_id: str) -> str:
        """Get a brief memory summary suitable for inclusion in conversation context.

        Args:
            operator_id: Operator ID

        Returns:
            Text suitable for inclusion in LLM context
        """
        memory = self.get_operator_memory(operator_id)
        if not memory:
            return ""

        return f"Learned operator patterns: {memory.summary}"


# Global instance
_memory_engine: Optional[MemoryEngine] = None


def get_memory_engine(data_dir: Path = Path("data")) -> MemoryEngine:
    """Get or create the global memory engine instance."""
    global _memory_engine
    if _memory_engine is None:
        _memory_engine = MemoryEngine(data_dir)
    return _memory_engine
