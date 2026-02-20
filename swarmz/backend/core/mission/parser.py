# Parser module for SWARMZ mission


class Parser:
    def parse(self, command):
        return {"id": "mission_1", "name": "Test Mission", "steps": [command]}


class MissionParser:
    def parse(self, mission_data):
        """Parse mission data into a Mission object."""
        return {"parsed": mission_data}
