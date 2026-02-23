# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Run module: orchestrates Galileo harness 4-stage pipeline
1. Load domain pack + generate hypothesis IDs
2. GENERATE hypotheses (LLM)
3. CRITIQUE each (LLM)
4. SPECIFY TEST (LLM experimentalist)
5. SCORE + accept/reject
6. Output packs
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .determinism import generate_ids, stableStringify
from .similarity import check_similarity
from .gates import apply_gates
from .scorer import score_hypothesis, should_accept
from .storage import (
    init_storage,
    load_hypotheses,
    load_priors,
    load_domain_pack,
    save_hypothesis,
    save_experiment,
    save_score,
    save_run_record,
)
from .prompts import get_generator_prompt, get_critic_prompt, get_experimentalist_prompt


def run_galileo(
    domain: str = "generic_local",
    seed: int = 12345,
    n_hypotheses: int = 5,
    llm_client=None,  # Optional LLM client (for actual LLM calls)
    use_synthetic: bool = True,  # If True, use synthetic generator for testing
) -> Dict[str, Any]:
    """
    Execute full Galileo harness pipeline.

    Args:
        domain: Domain name
        seed: Random seed for reproducibility
        n_hypotheses: Number of hypotheses to generate
        llm_client: LLM client (required for LLM stages) - MUST be provided by caller
        use_synthetic: If True and no llm_client, use synthetic test data

    Returns:
        Dict with run_id, accepted_hypothesis_ids, experiment_ids, file paths, etc.
    """
    # Initialize storage
    storage_dir = init_storage()

    # Generate deterministic IDs
    run_id, hypothesis_ids, experiment_ids = generate_ids(domain, seed, n_hypotheses)

    # Load domain pack
    domain_pack = load_domain_pack(domain)

    # Load priors for similarity checking
    priors = load_priors(domain)
    existing_hypotheses = load_hypotheses(domain)

    # Initialize run record
    run_record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "domain": domain,
        "seed": seed,
        "inputs_hash": stableStringify(
            {"domain": domain, "seed": seed, "n_hypotheses": n_hypotheses}
        ),
        "hypothesis_ids": list(hypothesis_ids.values()),
        "accepted_hypothesis_ids": [],
        "notes": "Galileo v0.1 run",
    }

    hypotheses = []
    accepted_ids = []
    experiments = []
    scores_list = []

    # --- STAGE 1: GENERATE hypotheses ---
    generated = _generate_hypotheses(
        domain,
        n_hypotheses,
        hypothesis_ids,
        domain_pack,
        seed,
        llm_client=llm_client,
        use_synthetic=use_synthetic,
    )
    hypotheses.extend(generated)

    # --- STAGE 2: CRITIQUE each ---
    for hyp in hypotheses:
        critique = _critique_hypothesis(
            hyp, domain, llm_client=llm_client, use_synthetic=use_synthetic
        )
        hyp["critique"] = critique

    # --- STAGE 3: SPECIFY TEST (LLM experimentalist) ---
    for hyp in hypotheses:
        experiment = _specify_experiment(
            hyp, domain, seed, llm_client=llm_client, use_synthetic=use_synthetic
        )
        hyp["experiment"] = experiment
        exp_full = {
            "experiment_id": experiment_ids[hyp["hypothesis_id"]],
            "hypothesis_id": hyp["hypothesis_id"],
            "domain": domain,
            "goal": experiment.get("goal", ""),
            "protocol": experiment.get("protocol", {}),
            "repro": experiment.get("repro", {}),
            "status": "DESIGNED",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        experiments.append(exp_full)

    # --- STAGE 5: SCORE rule-engine ---
    for hyp in hypotheses:
        # Similarity check
        similarity, closest_known, difference = check_similarity(
            hyp.get("claim", ""), priors, existing_hypotheses
        )
        hyp["novelty_anchor"] = {
            "closest_known": closest_known,
            "difference": difference,
        }

        # Apply gates
        gates_pass, gates_passed, gates_failed = apply_gates(
            hyp, similarity_score=similarity
        )

        # Score
        scores = score_hypothesis(
            hyp, similarity_score=similarity, gate_failures=gates_failed
        )

        # Accept/reject
        accept, reason = should_accept(scores, gate_failures=gates_failed)

        # Record score
        score_record = {
            "hypothesis_id": hyp["hypothesis_id"],
            "scores": scores,
            "gates_passed": gates_passed,
            "gates_failed": gates_failed,
            "decision": "ACCEPTED" if accept else "REJECTED",
            "reason": reason,
            "similarity_score": similarity,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        scores_list.append(score_record)

        # Set hypothesis status
        hyp["status"] = "ACCEPTED" if accept else "REJECTED"

        if accept:
            accepted_ids.append(hyp["hypothesis_id"])

    # --- SAVE records ---
    for hyp in hypotheses:
        save_hypothesis(hyp)

    for exp in experiments:
        save_experiment(exp)

    for score_rec in scores_list:
        save_score(score_rec)

    # Save run record
    run_record["accepted_hypothesis_ids"] = accepted_ids
    save_run_record(run_record)

    # --- OUTPUT packs ---
    packs_dir = Path(__file__).parent.parent / "packs" / "galileo" / run_id
    packs_dir.mkdir(parents=True, exist_ok=True)

    # Manifest
    manifest = {
        "run_id": run_id,
        "timestamp": run_record["timestamp"],
        "domain": domain,
        "seed": seed,
        "accepted_hypothesis_ids": accepted_ids,
        "total_hypotheses": len(hypotheses),
        "paths": {
            "hypotheses": "hypotheses.json",
            "experiments": "experiments.json",
            "scores": "scores.json",
            "run_instructions": "RUN_INSTRUCTIONS.md",
        },
    }

    with open(packs_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Hypotheses pack
    with open(packs_dir / "hypotheses.json", "w") as f:
        json.dump([h for h in hypotheses if h["status"] == "ACCEPTED"], f, indent=2)

    # Experiments pack
    with open(packs_dir / "experiments.json", "w") as f:
        json.dump(experiments, f, indent=2)

    # Scores pack
    with open(packs_dir / "scores.json", "w") as f:
        json.dump(scores_list, f, indent=2)

    # RUN_INSTRUCTIONS.md
    instructions = f"""# Galileo Run {run_id}

## Summary
- Domain: {domain}
- Seed: {seed}
- Total hypotheses generated: {len(hypotheses)}
- Accepted: {len(accepted_ids)}
- Timestamp: {run_record["timestamp"]}

## Accepted Hypotheses
"""
    for hyp_id in accepted_ids:
        hyp = next((h for h in hypotheses if h["hypothesis_id"] == hyp_id), None)
        if hyp:
            instructions += f"\n### {hyp['title']}\n"
            instructions += f"- Claim: {hyp['claim']}\n"
            instructions += f"- Test Outline: {hyp.get('test_outline', 'N/A')}\n"

    instructions += "\n## How to Run Experiments\n"
    instructions += "See experiments.json for full protocol details.\n"
    instructions += "All experiments are LOCAL ONLY (no external API calls).\n"
    instructions += "Operator-gated execution: ensure review before running.\n"

    with open(packs_dir / "RUN_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)

    return {
        "run_id": run_id,
        "accepted_hypothesis_ids": accepted_ids,
        "experiment_ids": list(experiment_ids.values()),
        "total_hypotheses": len(hypotheses),
        "total_accepted": len(accepted_ids),
        "paths": {
            "manifest": str(packs_dir / "manifest.json"),
            "hypotheses": str(packs_dir / "hypotheses.json"),
            "experiments": str(packs_dir / "experiments.json"),
            "scores": str(packs_dir / "scores.json"),
            "run_instructions": str(packs_dir / "RUN_INSTRUCTIONS.md"),
            "storage_dir": str(storage_dir),
        },
    }


def _generate_hypotheses(
    domain: str,
    n: int,
    hypothesis_ids: Dict,
    domain_pack: Dict,
    seed: int,
    llm_client=None,
    use_synthetic=False,
) -> List[Dict]:
    """Generate n hypotheses using LLM (or synthetic data if no LLM)."""
    hypotheses = []

    if llm_client and not use_synthetic:
        # Call actual LLM
        prompt = get_generator_prompt(domain, n, domain_pack, seed)
        # response = llm_client.generate(prompt)  # Not implemented yet
        # Parse response as JSON array
        raise NotImplementedError("LLM integration not yet implemented")
    else:
        # Generate synthetic hypotheses for testing
        hypotheses = _synthetic_hypotheses(domain, n, hypothesis_ids)

    return hypotheses


def _critique_hypothesis(
    hyp: Dict, domain: str, llm_client=None, use_synthetic=False
) -> Dict:
    """Critique a hypothesis using LLM (or synthetic if no LLM)."""
    if llm_client and not use_synthetic:
        prompt = get_critic_prompt(hyp, domain)
        # response = llm_client.generate(prompt)
        raise NotImplementedError("LLM integration not yet implemented")
    else:
        # Synthetic critique
        return {
            "strengths": ["Clear mechanism", "Falsifiable"],
            "confounders_additional": [],
            "strongest_counterargument": "Needs more testing",
            "duplication_hints": "Potentially novel",
            "testability_concerns": "Minor",
            "reasoning": "Synthetic critique for testing",
        }


def _specify_experiment(
    hyp: Dict, domain: str, seed: int, llm_client=None, use_synthetic=False
) -> Dict:
    """Design experiment protocol using LLM (or synthetic if no LLM)."""
    if llm_client and not use_synthetic:
        prompt = get_experimentalist_prompt(hyp, domain, seed)
        # response = llm_client.generate(prompt)
        raise NotImplementedError("LLM integration not yet implemented")
    else:
        # Synthetic experiment
        return {
            "goal": f"Test {hyp.get('title', 'hypothesis')}",
            "protocol": {
                "dataset": "./data/synthetic",
                "variables": {
                    "independent": ["treatment"],
                    "dependent": ["outcome"],
                    "controls": [],
                },
                "method": "simulation",
                "steps": ["Initialize", "Run simulation", "Analyze results"],
                "stopping_rule": "After 100 iterations",
                "success_criteria": "p-value < 0.05",
                "failure_criteria": "p-value >= 0.05",
            },
            "repro": {
                "seed": seed,
                "env": "local",
                "deps": [],
                "run_command": f"python -m galileo.synthetic_runner --seed {seed}",
                "expected_artifacts": ["results.json"],
            },
        }


def _synthetic_hypotheses(domain: str, n: int, hypothesis_ids: Dict) -> List[Dict]:
    """Generate synthetic test hypotheses."""
    hypotheses = []
    for idx in range(n):
        hyp = {
            "hypothesis_id": hypothesis_ids[idx],
            "domain": domain,
            "title": f"Synthetic hypothesis {idx + 1}",
            "claim": f"In {domain}, phenomenon X leads to outcome Y",
            "mechanism": "Direct causal link between X and Y",
            "predictions": ["+5% increase in metric Y when X is present"],
            "novelty_anchor": {
                "closest_known": "Generic baseline",
                "difference": "Specific to this domain",
            },
            "assumptions": ["Assumption 1", "Assumption 2"],
            "confounders": ["Potential confounder"],
            "required_data": ["data1.csv"],
            "test_outline": "Controlled simulation comparing X presence vs absence",
            "failure_criteria": ["Y does not increase by >= 3%"],
            "created_by": "galileo_generator_v1",
            "status": "PROPOSED",
        }
        hypotheses.append(hyp)

    return hypotheses
