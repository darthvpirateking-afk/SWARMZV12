# Engine module for SWARMZ runtime

import yaml
import json
from backend.core.governor.governor import Governor
from backend.core.patchpack.patchpack import Patchpack
from backend.core.session.session import Session
from backend.core.mission.parser import Parser
from backend.core.mission.planner import Planner
from backend.core.mission.executor import Executor
from backend.core.mission.reporter import Reporter
from backend.core.swarm.registry import Registry
from backend.core.swarm.behavior import BehaviorEngine
from backend.core.swarm.formation import FormationEngine
from backend.core.avatar.brain import Brain
from backend.core.avatar.state import State
from backend.core.avatar.presence import Presence
from backend.core.cosmology.mesh_router import MeshRouter


class Engine:
    def __init__(self):
        self.config = None
        self.mesh = None
        self.governor = None
        self.patchpack = None
        self.session = None
        self.mission_engine = None
        self.swarm_engine = None
        self.avatar = None

    def load_config(self):
        with open("config/settings.yaml", "r") as f:
            self.config = yaml.safe_load(f)

    def load_mesh(self):
        with open("mesh/nodes.json", "r") as f:
            nodes = json.load(f)
        with open("mesh/links.json", "r") as f:
            links = json.load(f)
        self.mesh = MeshRouter(nodes, links)

    def initialize_components(self):
        self.governor = Governor()
        self.patchpack = Patchpack()
        self.session = Session(operator_id="default_operator")
        self.mission_engine = {
            "parser": Parser(),
            "planner": Planner(),
            "executor": Executor(),
            "reporter": Reporter(),
        }
        self.swarm_engine = {
            "registry": Registry(),
            "behavior": BehaviorEngine(),
            "formation": FormationEngine(),
        }
        self.avatar = {"brain": Brain(), "state": State(), "presence": Presence()}
