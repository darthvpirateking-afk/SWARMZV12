# Audit module for SWARMZ governor


class Audit:
    def __init__(self):
        self.logs = []

    def log_action(self, user, action):
        entry = {"user": user, "action": action}
        self.logs.append(entry)
        print(f"Audit log: {entry}")

    def get_logs(self):
        return self.logs
