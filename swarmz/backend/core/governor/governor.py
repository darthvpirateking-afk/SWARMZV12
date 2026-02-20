# Governor module for SWARMZ core

class Governor:
    def __init__(self):
        self.shadow_ledger = []

    def validate(self, operation):
        return True

    def block(self, operation):
        self.shadow_ledger.append(operation)