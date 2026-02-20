# SWARMZ Swarm Engine v3
# Adaptive and Dynamic Task Routing

from typing import Dict, Any, List
from datetime import datetime


class SwarmEngineV3:
    def __init__(self):
        self.workers = []
        self.task_queue = []
        self.routing_table = {}

    def register_worker(self, worker_id: str, capabilities: List[str]):
        """Register a new worker with specific capabilities."""
        self.workers.append(
            {"id": worker_id, "capabilities": capabilities, "status": "idle"}
        )

    def add_task(self, task_id: str, task_type: str, payload: Dict[str, Any]):
        """Add a new task to the queue."""
        self.task_queue.append(
            {"id": task_id, "type": task_type, "payload": payload, "status": "pending"}
        )

    def route_task(self):
        """Route tasks to available workers based on capabilities."""
        for task in self.task_queue:
            if task["status"] == "pending":
                for worker in self.workers:
                    if (
                        task["type"] in worker["capabilities"]
                        and worker["status"] == "idle"
                    ):
                        self._assign_task_to_worker(task, worker)
                        break

    def _assign_task_to_worker(self, task: Dict[str, Any], worker: Dict[str, Any]):
        """Assign a task to a worker."""
        task["status"] = "in_progress"
        worker["status"] = "busy"
        worker["current_task"] = task["id"]
        print(f"Task {task['id']} assigned to Worker {worker['id']}")

    def complete_task(self, worker_id: str):
        """Mark a task as complete and free the worker."""
        for worker in self.workers:
            if worker["id"] == worker_id and worker["status"] == "busy":
                task_id = worker.pop("current_task", None)
                worker["status"] = "idle"
                for task in self.task_queue:
                    if task["id"] == task_id:
                        task["status"] = "completed"
                        print(f"Task {task_id} completed by Worker {worker_id}")
                        break

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the swarm engine."""
        return {
            "workers": self.workers,
            "tasks": self.task_queue,
            "timestamp": datetime.now().isoformat(),
        }
