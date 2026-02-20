# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
# SWARMZ Extension Registry
# Purpose: Allow future add-only modules to register themselves safely.

class ExtensionRegistry:
    def __init__(self):
        self.extensions = {}

    def register_extension(self, name, metadata):
        try:
            self.extensions[name] = metadata
        except Exception as e:
            pass  # Fail-open: Skip on error

    def list_extensions(self):
        try:
            return list(self.extensions.keys())
        except Exception as e:
            return []  # Fail-open: Return empty list

    def get_extension(self, name):
        try:
            return self.extensions.get(name, None)
        except Exception as e:
            return None  # Fail-open
