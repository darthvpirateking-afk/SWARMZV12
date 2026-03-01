# state.py
# Manages avatar state.


class AvatarState:
    def __init__(self):
        self.avatar_form = {}
        self.mission_context = {}

    def update_state(self, key, value):
        """Update the avatar state."""
        self.avatar_form[key] = value

    def get_state(self):
        """Retrieve the current state."""
        return self.avatar_form
