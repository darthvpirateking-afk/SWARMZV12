# Parser module for SWARMZ mission


class Parser:
    def parse(self, command):
        return {"id": "mission_1", "name": "Test Mission", "steps": [command]}


class MissionParser:
    def parse(self, mission_data):
        """Parse mission data."""
        return {"parsed": mission_data}

    def parse(self, command):
        """
        Convert operator command into a Mission object.
        """
        pass
