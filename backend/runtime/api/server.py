# SWARMZ API server

from backend.runtime.core.engine import SwarmzEngine, MissionEngine, SwarmEngine
from backend.runtime.core.telemetry import Telemetry
from backend.runtime.core.autoloop import AutoLoop
from backend.runtime.storage.db import Database
from backend.governor.permissions import Permissions
from backend.governor.audit import Audit
from backend.patchpack.loader import Loader
from backend.patchpack.validator import Validator

# Activation sequence
if __name__ == "__main__":
    print("Starting SWARMZ system...")

    # Initialize components
    telemetry = Telemetry()
    database = Database()
    permissions = Permissions()
    audit = Audit()
    loader = Loader()
    validator = Validator()

    swarmz_engine = SwarmzEngine()
    mission_engine = MissionEngine()
    swarm_engine = SwarmEngine()

    autoloop = AutoLoop(interval=5)

    # Start autoloop
    autoloop.start()

    print("SWARMZ system ignition complete.")
