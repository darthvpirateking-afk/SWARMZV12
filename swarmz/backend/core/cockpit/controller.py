# controller.py
# Controls cockpit operations.

class CockpitController:
    def control(self, command):
        """Control the cockpit."""
        return {"status": "controlled", "command": command}
