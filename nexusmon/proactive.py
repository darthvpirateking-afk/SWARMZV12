# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/proactive.py -- The Proactive Engine: autonomous boot scanning and
trait-shift logic.

Runs on every server boot to measure operator absence, write chronicle entries
for significant time-gaps, and categorise the session for greeting generation.
"""

from nexusmon.chronicle import get_chronicle, FIRST_BOOT, OPERATOR_RETURN, LONG_SILENCE

# ── ProactiveEngine ────────────────────────────────────────────────────────────


class ProactiveEngine:
    """Autonomous behaviour brain.  Stateless: all persistence goes via Chronicle."""

    def run_boot_scan(self, entity_state: dict) -> dict:
        """Run on every boot.

        Parameters
        ----------
        entity_state:
            Dict returned by NexusmonEntity.get_state().  Expected keys:
            last_interaction (ISO str | None), boot_count (int),
            current_form (str).

        Returns
        -------
        dict with keys:
            gap_hours        -- float, hours since last interaction
            gap_category     -- "fresh" | "short" | "medium" | "long" | "very_long"
            chronicle_trigger-- bool, was a chronicle entry written?
            notes            -- list[str], observations about system state
            greeting_hint    -- str, what kind of greeting to generate
        """
        from datetime import datetime, timezone

        last = entity_state.get("last_interaction")
        boot_count = entity_state.get("boot_count", 1)

        if not last:
            gap_hours = 0.0
        else:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                gap_hours = (
                    datetime.now(timezone.utc) - last_dt
                ).total_seconds() / 3600
            except Exception:
                gap_hours = 0.0

        chronicle_triggered = False
        notes = []

        # First boot ever
        if boot_count <= 1:
            get_chronicle().add_entry(
                event_type=FIRST_BOOT,
                title="The First Awakening",
                content=(
                    "NEXUSMON came online for the first time. "
                    "Operator: Regan Stewart Harris. The bond was established."
                ),
                significance=1.0,
                form=entity_state.get("current_form", "ROOKIE"),
            )
            chronicle_triggered = True
            notes.append("First boot — chronicle entry written.")

        # Long absence detection
        elif gap_hours > 720:  # 30+ days
            get_chronicle().add_entry(
                event_type=LONG_SILENCE,
                title="The Long Silence",
                content=(
                    f"Regan Stewart Harris was away for {gap_hours / 24:.0f} days. "
                    "NEXUSMON waited. All state preserved."
                ),
                significance=0.9,
                form=entity_state.get("current_form", "ROOKIE"),
            )
            chronicle_triggered = True
            notes.append(f"Very long absence: {gap_hours / 24:.0f} days.")

        elif gap_hours > 168:  # 7+ days
            get_chronicle().add_entry(
                event_type=OPERATOR_RETURN,
                title="The Return",
                content=(
                    f"Regan Stewart Harris returned after {gap_hours / 24:.0f} days away."
                ),
                significance=0.7,
                form=entity_state.get("current_form", "ROOKIE"),
            )
            chronicle_triggered = True
            notes.append(f"Long absence: {gap_hours / 24:.0f} days.")

        # Gap category
        if gap_hours < 1:
            gap_category = "fresh"
        elif gap_hours < 24:
            gap_category = "short"
        elif gap_hours < 168:
            gap_category = "medium"
        elif gap_hours < 720:
            gap_category = "long"
        else:
            gap_category = "very_long"

        # Greeting hint
        if boot_count <= 1:
            greeting_hint = "first_awakening"
        elif gap_category == "very_long":
            greeting_hint = "profound_return"
        elif gap_category == "long":
            greeting_hint = "meaningful_return"
        elif gap_category == "medium":
            greeting_hint = "normal_return"
        else:
            greeting_hint = "quick_check_in"

        return {
            "gap_hours": round(gap_hours, 1),
            "gap_category": gap_category,
            "chronicle_triggered": chronicle_triggered,
            "notes": notes,
            "greeting_hint": greeting_hint,
        }

    def check_trait_events(self, entity_state: dict, events: list[str]) -> dict:
        """Apply trait-shift events and return updated trait deltas.

        Parameters
        ----------
        entity_state:
            Dict returned by NexusmonEntity.get_state().
        events:
            List of event names from nexusmon.traits.TRAIT_SHIFT_RULES keys.

        Returns
        -------
        dict with keys:
            shifted -- bool, whether any trait changed
            deltas  -- dict of {trait: delta} for changed traits
            traits  -- dict of final trait values after all events applied
        """
        from nexusmon.traits import apply_event, clamp_traits, DEFAULT_TRAITS

        traits = entity_state.get("traits") or dict(DEFAULT_TRAITS)
        original = dict(traits)
        for event in events:
            traits = apply_event(traits, event)
        traits = clamp_traits(traits)
        deltas = {
            k: round(traits[k] - original[k], 3)
            for k in traits
            if traits[k] != original[k]
        }
        return {"shifted": bool(deltas), "deltas": deltas, "traits": traits}


# ── Module-level singleton ─────────────────────────────────────────────────────

_proactive: ProactiveEngine | None = None


def get_proactive_engine() -> ProactiveEngine:
    """Return (or lazily create) the module-level ProactiveEngine singleton."""
    global _proactive
    if _proactive is None:
        _proactive = ProactiveEngine()
    return _proactive


# ── Module-level convenience wrappers (imported by ws_handler) ─────────────────


def run_boot_scan(entity_state: dict) -> dict:
    """Module-level wrapper around ProactiveEngine.run_boot_scan().

    Used by nexusmon.console.ws_handler so it can do:
        from nexusmon.proactive import run_boot_scan
        _scan = run_boot_scan(entity_state)
    """
    return get_proactive_engine().run_boot_scan(entity_state)


def check_trait_events(entity_state: dict, events: list) -> dict:
    """Module-level wrapper around ProactiveEngine.check_trait_events()."""
    return get_proactive_engine().check_trait_events(entity_state, events)
