class IntegrationMap:
    def __init__(self):
        self.nodes = {
            "cockpit_core": None,
            "operator_avatar": None,
            "mission_engine": None,
            "swarm_engine": None,
            "cosmology_layer": None,
            "patchpack_engine": None,
            "shadow_ledger": None,
            "operator_session": None,
            "governor": None,
            "backend_nucleus": None,
            "ui_shell": None,
        }
        self.flows = []

    def define_flow(self, source, target):
        self.flows.append((source, target))

    def get_integration_map(self):
        return {
            "nodes": self.nodes,
            "flows": self.flows,
        }


# Example usage
integration_map = IntegrationMap()
integration_map.define_flow("cockpit_core", "operator_avatar")
integration_map.define_flow("operator_avatar", "mission_engine")
integration_map.define_flow("mission_engine", "governor")
integration_map.define_flow("governor", "swarm_engine")
integration_map.define_flow("swarm_engine", "cosmology_layer")
integration_map.define_flow("cosmology_layer", "cockpit_core")
integration_map.define_flow("patchpack_engine", "mission_engine")
integration_map.define_flow("shadow_ledger", "governor")
integration_map.define_flow("operator_session", "operator_avatar")
integration_map.define_flow("backend_nucleus", "ui_shell")
