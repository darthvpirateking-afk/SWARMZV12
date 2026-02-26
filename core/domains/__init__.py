from core.domains.bio_lab import BioLabGateway
from core.domains.space_mission import SpaceMissionInterface
from core.domains.software_dev import SoftwareDevWorker
from core.domains.data_science import DataScienceWorker
from core.domains.security import SecurityWorker
from core.domains.infrastructure import InfrastructureWorker
from core.domains.research import ResearchWorker
from core.domains.financial import FinancialWorker
from core.domains.physical_builder import PhysicalBuilderWorker
from core.domains.strategic_advisor import StrategicAdvisorWorker
from core.domains.system_health import SystemHealthWorker

# Domain worker registry for capability progression
DOMAIN_WORKERS = {
    "bio_lab": BioLabGateway,
    "space_mission": SpaceMissionInterface,
    "software_dev": SoftwareDevWorker,
    "data_science": DataScienceWorker,
    "security": SecurityWorker,
    "infrastructure": InfrastructureWorker,
    "research": ResearchWorker,
    "financial": FinancialWorker,
    "physical_builder": PhysicalBuilderWorker,
    "strategic_advisor": StrategicAdvisorWorker,
    "system_health": SystemHealthWorker,
}

# Domain unlock progression by rank/XP
DOMAIN_UNLOCK_REQUIREMENTS = {
    "system_health": {"rank": "E", "xp_min": 0},  # Always available - personal worker
    "bio_lab": {"rank": "D", "xp_min": 0},  # Starter domain
    "space_mission": {"rank": "D", "xp_min": 0},  # Starter domain
    "software_dev": {"rank": "C", "xp_min": 100},  # Unlocks at C rank
    "data_science": {"rank": "C", "xp_min": 250},  # Unlocks mid-C rank
    "strategic_advisor": {"rank": "B", "xp_min": 400},  # Decision support
    "security": {"rank": "B", "xp_min": 500},  # Unlocks at B rank
    "financial": {"rank": "B", "xp_min": 650},  # Money operations
    "infrastructure": {"rank": "B", "xp_min": 750},  # Unlocks mid-B rank
    "physical_builder": {"rank": "A", "xp_min": 900},  # Real-world building
    "research": {"rank": "A", "xp_min": 1000},  # Unlocks at A rank
}

def get_available_domains(rank: str, xp: float) -> list:
    """Get domains available at current rank/XP level."""
    rank_order = ["E", "D", "C", "B", "A", "S", "N"]
    current_rank_index = rank_order.index(rank) if rank in rank_order else 0
    
    available = []
    for domain, reqs in DOMAIN_UNLOCK_REQUIREMENTS.items():
        req_rank = reqs["rank"]
        req_xp = reqs["xp_min"]
        req_rank_index = rank_order.index(req_rank)
        
        if current_rank_index >= req_rank_index and xp >= req_xp:
            available.append(domain)
    
    return available
