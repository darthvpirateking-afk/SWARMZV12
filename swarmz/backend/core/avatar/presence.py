# presence.py
# Surfaces system state.

class AvatarPresence:
    def surface_system_state(self, state):
        """Surface the system state."""
        return f"System State: {state}"

    def render(self, state):
        """
        Render avatar state to cockpit.
        """
        return {"avatar_state": state.avatar_form, "mission_context": state.mission_context}
