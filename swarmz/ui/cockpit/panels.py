# panels.py
# Implements the Cockpit panels.

class AvatarPanel:
    def display(self):
        return "Avatar Panel Displayed"

class MissionsPanel:
    def display(self):
        return "Missions Panel Displayed"

class SwarmPanel:
    def display(self):
        return "Swarm Panel Displayed"

class CosmologyPanel:
    def display(self):
        return "Cosmology Panel Displayed"

class PatchpackPanel:
    def display(self):
        return "Patchpack Panel Displayed"

class SystemPanel:
    def display(self):
        return "System Panel Displayed"

# Example usage
if __name__ == "__main__":
    avatar_panel = AvatarPanel()
    missions_panel = MissionsPanel()
    swarm_panel = SwarmPanel()
    cosmology_panel = CosmologyPanel()
    patchpack_panel = PatchpackPanel()
    system_panel = SystemPanel()

    print(avatar_panel.display())
    print(missions_panel.display())
    print(swarm_panel.display())
    print(cosmology_panel.display())
    print(patchpack_panel.display())
    print(system_panel.display())