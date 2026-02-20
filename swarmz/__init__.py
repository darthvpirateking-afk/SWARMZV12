"""Expose core SWARMZ classes for legacy imports.

This package-level shim loads the top-level ``swarmz.py`` module (which
contains ``SwarmzCore``, ``OperatorSovereignty``, and ``TaskExecutor``) so that
``from swarmz import SwarmzCore`` continues to work even though ``swarmz`` is a
package directory.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_core_path = Path(__file__).resolve().parent.parent / "swarmz.py"
_spec = spec_from_file_location("swarmz_core_legacy", _core_path)
_module = module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_module)

SwarmzCore = _module.SwarmzCore
OperatorSovereignty = _module.OperatorSovereignty
TaskExecutor = _module.TaskExecutor

__all__ = ["SwarmzCore", "OperatorSovereignty", "TaskExecutor"]
