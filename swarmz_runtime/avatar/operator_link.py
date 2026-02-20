class OperatorLink:
    def __init__(self):
        self.state = "link_idle"
        self.channels = {
            "identity_sync": False,
            "mission_sync": False,
            "cosmology_sync": False,
            "swarm_sync": False,
        }

    def initiate_link(self, state):
        if state in ["link_idle", "link_sync", "link_focus", "link_overclock", "link_shadow"]:
            self.state = state
            return f"Link state set to {state}"
        raise ValueError("Invalid link state")

    def update_channel(self, channel, status):
        if channel in self.channels:
            self.channels[channel] = status
            return f"Channel {channel} updated to {status}"
        raise ValueError("Invalid channel")

    def get_link_state(self):
        return {
            "state": self.state,
            "channels": self.channels,
        }