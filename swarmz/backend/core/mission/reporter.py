# reporter.py
# Reports mission status.


class MissionReporter:
    def report(self, mission):
        """
        Report mission state to cockpit.
        """
        return mission.get("state", "unknown")
