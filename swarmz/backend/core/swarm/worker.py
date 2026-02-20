# worker.py
# Represents a swarm worker.

class SwarmWorker:
    def __init__(self, id):
        self.id = id

    def perform_task(self, task):
        """Perform a task."""
        return {"worker_id": self.id, "task": task, "status": "completed"}
