# Permissions module for SWARMZ governor


class Permissions:
    def __init__(self):
        self.permissions = {}

    def grant(self, user, action):
        self.permissions[(user, action)] = True
        print(f"Granted {action} to {user}")

    def revoke(self, user, action):
        self.permissions[(user, action)] = False
        print(f"Revoked {action} from {user}")

    def check(self, user, action):
        return self.permissions.get((user, action), False)
