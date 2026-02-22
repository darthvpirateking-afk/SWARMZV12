class ThroneGovernance:
    """
    ThroneGovernance
    ----------------
    - Encodes operator sovereignty.
    - No autonomy, no self-starting, no self-modification.
    """

    def __init__(self, operator_id: str | None = None):
        self.operator_id = operator_id

    def assert_operator_control(self) -> None:
        # Placeholder hook: in real system, verify operator session / context.
        # This is where you'd enforce:
        # - no background execution
        # - no self-initiated actions
        # - no state changes without explicit operator command
        return

    def allow_action(self, action_name: str) -> bool:
        # Could be extended with policy checks.
        return True

    def describe_constraints(self) -> dict:
        return {
            "autonomy": "disabled",
            "self_modification": "disabled",
            "emotional_simulation": "disabled",
            "operator_approval_required": True,
        }
