# Loader module for SWARMZ patchpack

class Loader:
    def __init__(self):
        self.patches = []

    def load_patch(self, patch):
        self.patches.append(patch)
        print(f"Loaded patch: {patch}")