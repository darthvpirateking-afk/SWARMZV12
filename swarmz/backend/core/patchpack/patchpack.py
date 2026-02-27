# Patchpack module for SWARMZ core


class Patchpack:
    """
    Append-only log of all system patches.
    """

    def __init__(self):
        self.patches = []

    def append(self, patch):
        self.patches.append(patch)

    def list(self):
        return self.patches


# Example usage
if __name__ == "__main__":
    patchpack = Patchpack()
    patchpack.append("update", {"key": "value"})
    print("Patchpack Entries:", patchpack.list())
