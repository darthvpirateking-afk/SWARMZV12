# brain.py
# Parses operator commands.

class AvatarBrain:
    def parse_command(self, command):
        """
        Convert operator command into mission ops.
        """
        return {"type": "create", "payload": {"command": command}}
