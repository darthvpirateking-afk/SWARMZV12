class ShadowLedger:
    def __init__(self):
        self.entries = []
        self.state = "clear"

    def append_entry(self, entry_type, details):
        self.entries.append({"type": entry_type, "details": details})
        self._update_state(entry_type)

    def _update_state(self, entry_type):
        if entry_type in ["depth_violation", "unbounded_op", "forbidden_kernel"]:
            self.state = "shadowed"
        elif entry_type == "entropy_overload":
            self.state = "lockdown"
        elif self.state == "clear":
            self.state = "warning"

    def get_ledger_state(self):
        return self.state

    def get_entries(self):
        return self.entries