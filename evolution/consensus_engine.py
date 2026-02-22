from typing import Any, Dict, List


def propose_upgrade(proposal: Dict[str, Any], simulation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Propose an upgrade only when at least one novel causal chain exists."""
    chains: List[Dict[str, Any]] = simulation_results.get("causal_chains", []) if simulation_results else []
    novel = [c for c in chains if c.get("novel") is True]

    if not novel:
        return {
            "accepted": False,
            "reason": "no_novel_causal_chain",
            "proposal": proposal,
        }

    return {
        "accepted": True,
        "reason": "novel_causal_chain_present",
        "proposal": proposal,
        "novel_chains": novel,
    }
