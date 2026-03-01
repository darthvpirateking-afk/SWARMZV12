# SWARMZ Reality-Engine v4
# Multi-Physics Layering

from typing import Dict, Any


class PhysicsLayer:
    def __init__(self, name: str, properties: Dict[str, Any]):
        self.name = name
        self.properties = properties


class RealityEngineV4:
    def __init__(self):
        self.layers = []

    def add_layer(self, layer: PhysicsLayer):
        """Add a new physics layer."""
        self.layers.append(layer)

    def adapt_to_layer(self, layer_name: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt an entity to a specific physics layer's properties and constraints.

        Merges the layer's property overrides into the entity dict and returns
        the adapted copy. Raises ValueError if the layer is not found.
        """
        layer = next((l for l in self.layers if l.name == layer_name), None)
        if not layer:
            raise ValueError(f"Physics layer {layer_name!r} not found")

        adapted = dict(entity)
        # Apply layer constraints: scale, gravity multiplier, entropy factor, etc.
        for key, value in layer.properties.items():
            constraint_key = f"layer_{key}"
            adapted[constraint_key] = value

        adapted["active_layer"] = layer_name
        return adapted

    def get_layer_properties(self, layer_name: str) -> Dict[str, Any]:
        """Retrieve properties of a specific physics layer."""
        layer = next((l for l in self.layers if l.name == layer_name), None)
        if not layer:
            raise ValueError(f"Physics layer {layer_name!r} not found")
        return layer.properties
