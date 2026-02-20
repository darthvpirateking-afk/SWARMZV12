class EntropyModel:
    def __init__(self):
        self.entropy_states = {}

    def drift_entropy(self, system_id: str, risk_level: float):
        self.entropy_states[f"drift:{system_id}"] = risk_level

    def shadow_entropy(self, operation_id: str, restriction_level: float):
        self.entropy_states[f"shadow:{operation_id}"] = restriction_level

    def patch_entropy(self, patch_id: str, density: float):
        self.entropy_states[f"patch:{patch_id}"] = density

    def get_entropy_state(self):
        return self.entropy_states