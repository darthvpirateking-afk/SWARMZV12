import logging

logger = logging.getLogger(__name__)


class ExternalExtensionAPI:
    def __init__(self):
        self.registered_extensions = {}

    def register_extension(self, name: str, capabilities: list):
        """Provide a controlled API for integrating vetted external knowledge modules."""
        self.registered_extensions[name] = {
            "capabilities": capabilities,
            "status": "active",
        }
        logger.info(f"Registered external extension: {name}")

    def invoke_extension(self, name: str, action: str, payload: dict):
        if name not in self.registered_extensions:
            return {"error": f"Extension {name} not found"}

        ext = self.registered_extensions[name]
        if action not in ext["capabilities"]:
            return {"error": f"Action {action} not supported by {name}"}

        logger.info(f"Invoking {action} on extension {name}")
        # Mock invocation
        return {"status": "success", "result": f"Executed {action} via {name}"}


extension_api = ExternalExtensionAPI()
