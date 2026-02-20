# models.py
# Defines avatar-related models.

class Avatar:
    def __init__(self, name, attributes):
        self.name = name
        self.attributes = attributes

    def __repr__(self):
        return f"Avatar(name={self.name}, attributes={self.attributes})"
