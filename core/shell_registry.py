# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Shell Registry Module

Provides a read-only registry of installed modules and their metadata.
"""

from typing import Dict, Any
from core.extension_registry import ExtensionRegistry

# Singleton registry instance
_registry = ExtensionRegistry()


def register_module(name: str, metadata: Dict[str, Any]) -> None:
    """Register a module with the shell registry."""
    _registry.register_extension(name, metadata)


def list_modules() -> Dict[str, Any]:
    """List all registered modules."""
    return {name: _registry.get_extension(name) for name in _registry.list_extensions()}


def self_check() -> Dict[str, Any]:
    """Perform a lightweight self-check of the registry."""
    return {
        "ok": True,
        "registered_modules": len(_registry.list_extensions()),
    }

