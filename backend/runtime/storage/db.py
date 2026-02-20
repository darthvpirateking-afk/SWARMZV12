# Database module for SWARMZ runtime

class Database:
    def __init__(self):
        self.storage = {}

    def save(self, key, value):
        self.storage[key] = value
        print(f"Saved {key}: {value}")

    def load(self, key):
        return self.storage.get(key, None)