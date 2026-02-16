"""
Determinism module: ensures reproducible outputs given same inputs
- Stable JSON stringification (sorted keys, stable arrays)
- Deterministic hashing and ID generation
- Seeded RNG for reproducibility
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Tuple


def stableStringify(obj: Any) -> str:
    """
    Recursively stringify object with sorted keys and stable ordering.
    No random key order, deterministic output.
    
    Args:
        obj: Any Python object
        
    Returns:
        Deterministic JSON string representation
    """
    return json.dumps(
        obj,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
        ensure_ascii=True
    )


def hash_sha256(data: str) -> str:
    """
    SHA256 hash of string data, return hex.
    
    Args:
        data: String to hash
        
    Returns:
        Hex SHA256 hash
    """
    return hashlib.sha256(data.encode()).hexdigest()


def inputs_hash(domain: str, seed: int, n_hypotheses: int, domain_pack_hash: str = "", priors_version: str = "v1") -> str:
    """
    Deterministic hash of input parameters.
    
    Args:
        domain: Domain (e.g., "biology", "physics")
        seed: Random seed (int)
        n_hypotheses: Number of hypotheses to generate
        domain_pack_hash: Hash of domain pack (optional)
        priors_version: Version of priors used (default "v1")
        
    Returns:
        SHA256 hex hash
    """
    inputs = {
        "domain": domain,
        "seed": seed,
        "n_hypotheses": n_hypotheses,
        "domain_pack_hash": domain_pack_hash,
        "priors_version": priors_version
    }
    return hash_sha256(stableStringify(inputs))


def generate_ids(domain: str, seed: int, n_hypotheses: int) -> Tuple[str, Dict[int, str], Dict[str, str]]:
    """
    Generate deterministic IDs for run, hypotheses, and experiments.
    
    Args:
        domain: Domain name
        seed: Random seed
        n_hypotheses: Number of hypotheses
        
    Returns:
        Tuple of (run_id, hypothesis_ids_dict {index: id}, experiment_ids_dict {hyp_id: exp_id})
    """
    now = datetime.utcnow()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    
    # Compute input hash
    inp_hash_full = inputs_hash(domain, seed, n_hypotheses)
    inp_hash_8 = inp_hash_full[:8]
    
    # run_id: G-YYYYMMDD-HHMMSS-{8hex}
    run_id = f"G-{date_str}-{time_str}-{inp_hash_8}"
    
    # hypothesis_ids: H-YYYYMMDD-{8hex(run_id + index)}
    hypothesis_ids = {}
    for idx in range(n_hypotheses):
        hyp_hash_input = f"{run_id}_{idx}"
        hyp_hash_full = hash_sha256(hyp_hash_input)
        hyp_hash_8 = hyp_hash_full[:8]
        hypothesis_ids[idx] = f"H-{date_str}-{hyp_hash_8}"
    
    # experiment_ids: E-YYYYMMDD-{8hex(hypothesis_id)}
    experiment_ids = {}
    for idx, hyp_id in hypothesis_ids.items():
        exp_hash_full = hash_sha256(hyp_id)
        exp_hash_8 = exp_hash_full[:8]
        experiment_ids[hyp_id] = f"E-{date_str}-{exp_hash_8}"
    
    return run_id, hypothesis_ids, experiment_ids
