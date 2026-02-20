class KernelRegistry:
    def __init__(self):
        self.kernels = {}

    def register_kernel(self, kernel_id, kernel_type):
        if kernel_id not in self.kernels:
            self.kernels[kernel_id] = {
                "type": kernel_type,
                "state": "idle",
            }
            return f"Kernel {kernel_id} registered as {kernel_type}"
        return f"Kernel {kernel_id} already exists"

    def update_kernel_state(self, kernel_id, state):
        if kernel_id in self.kernels:
            self.kernels[kernel_id]["state"] = state
            return f"Kernel {kernel_id} state updated to {state}"
        return f"Kernel {kernel_id} not found"

    def get_kernels(self):
        return self.kernels

class FederationRouter:
    def __init__(self, registry):
        self.registry = registry

    def route_task(self, kernel_id, task):
        if kernel_id in self.registry.kernels:
            kernel = self.registry.kernels[kernel_id]
            if kernel["state"] != "shadowed":
                return f"Task routed to {kernel_id} ({kernel['type']})"
            return f"Kernel {kernel_id} is shadowed, task blocked"
        return f"Kernel {kernel_id} not found"