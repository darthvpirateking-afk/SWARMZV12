# models.py
# Defines swarm-related models.


class SwarmTask:
    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return f"SwarmTask(description={self.description})"
