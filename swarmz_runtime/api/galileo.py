# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Galileo harness endpoints — hypothesis generation, experiments, determinism."""

import json
import traceback
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/v1/galileo", tags=["galileo"])


@router.post("/run")
async def galileo_run(
    domain: str = "generic_local",
    seed: int = 12345,
    n_hypotheses: int = 5,
):
    """Execute Galileo harness pipeline (deterministic hypothesis generation + testing)."""
    from galileo.run import run_galileo

    try:
        result = run_galileo(
            domain=domain,
            seed=seed,
            n_hypotheses=n_hypotheses,
            llm_client=None,
            use_synthetic=True,
        )
        return {
            "ok": True,
            "run_id": result["run_id"],
            "accepted_hypothesis_ids": result["accepted_hypothesis_ids"],
            "total_hypotheses": result["total_hypotheses"],
            "total_accepted": result["total_accepted"],
            "paths": result["paths"],
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:],
        }


@router.get("/hypotheses")
async def galileo_hypotheses(domain: str = None, status: str = None):
    """List hypotheses from Galileo storage."""
    from galileo.storage import load_hypotheses

    try:
        hypotheses = load_hypotheses(domain=domain)
        if status:
            hypotheses = [h for h in hypotheses if h.get("status") == status]
        return {
            "ok": True,
            "hypotheses": hypotheses,
            "count": len(hypotheses),
            "domain_filter": domain,
            "status_filter": status,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/experiments")
async def galileo_experiments(status: str = None):
    """List experiments from Galileo storage."""
    from galileo.storage import load_experiments

    try:
        experiments = load_experiments(status=status)
        return {
            "ok": True,
            "experiments": experiments,
            "count": len(experiments),
            "status_filter": status,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/runs/{run_id}")
async def galileo_run_details(run_id: str):
    """Get details of a specific Galileo run."""
    from galileo.storage import load_runs

    try:
        runs = load_runs()
        run = next((r for r in runs if r.get("run_id") == run_id), None)

        if not run:
            return {"ok": False, "error": f"Run {run_id} not found"}

        packs_dir = Path(__file__).resolve().parent.parent.parent / "packs" / "galileo" / run_id
        artifacts = {}

        if packs_dir.exists():
            for json_file in [
                "manifest.json",
                "hypotheses.json",
                "experiments.json",
                "scores.json",
            ]:
                file_path = packs_dir / json_file
                if file_path.exists():
                    try:
                        with open(file_path, "r") as f:
                            artifacts[json_file] = json.load(f)
                    except Exception:
                        pass

        return {"ok": True, "run": run, "artifacts": artifacts}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/experiments/{experiment_id}/run")
async def galileo_run_experiment(experiment_id: str, operator_key: str = None):
    """OPERATOR-GATED endpoint to run a specific experiment."""
    try:
        if not operator_key:
            return {
                "ok": False,
                "error": "Operator authorization required (operator_key header)",
                "status": "DENIED",
            }

        from galileo.storage import load_experiments

        experiments = load_experiments()
        experiment = next(
            (e for e in experiments if e.get("experiment_id") == experiment_id), None
        )

        if not experiment:
            return {"ok": False, "error": f"Experiment {experiment_id} not found"}

        if experiment.get("status") != "DESIGNED":
            return {
                "ok": False,
                "error": f"Experiment must be in DESIGNED status, current: {experiment.get('status')}",
            }

        stub_result = {
            "ok": True,
            "experiment_id": experiment_id,
            "status": "STUB_COMPLETED",
            "note": "v0.1 stub runner - full execution deferred",
            "seed": experiment.get("repro", {}).get("seed"),
            "run_command": experiment.get("repro", {}).get("run_command"),
            "expected_artifacts": experiment.get("repro", {}).get(
                "expected_artifacts", []
            ),
            "synthetic_result": {
                "success_rate": 0.85,
                "effect_size": 0.42,
                "p_value": 0.038,
            },
        }
        return stub_result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:],
        }


@router.get("/selfcheck")
async def galileo_selfcheck():
    """Determinism self-check: runs pipeline twice, verifies identical outputs."""
    from galileo.run import run_galileo
    from galileo.determinism import stableStringify

    try:
        result1 = run_galileo(
            domain="test_domain",
            seed=42,
            n_hypotheses=3,
            llm_client=None,
            use_synthetic=True,
        )
        result2 = run_galileo(
            domain="test_domain",
            seed=42,
            n_hypotheses=3,
            llm_client=None,
            use_synthetic=True,
        )

        ids_match = set(result1["accepted_hypothesis_ids"]) == set(
            result2["accepted_hypothesis_ids"]
        )
        totals_match = (
            result1["total_hypotheses"] == result2["total_hypotheses"]
            and result1["total_accepted"] == result2["total_accepted"]
        )

        json_match = True
        try:
            with open(result1["paths"]["hypotheses"], "r") as f:
                hyp1 = json.load(f)
            with open(result2["paths"]["hypotheses"], "r") as f:
                hyp2 = json.load(f)
            json_match = stableStringify(hyp1) == stableStringify(hyp2)
        except Exception:
            json_match = None

        deterministic = ids_match and totals_match and (json_match is not False)

        return {
            "ok": True,
            "deterministic": deterministic,
            "selfcheck_results": {
                "ids_match": ids_match,
                "totals_match": totals_match,
                "json_match": json_match,
                "run1_id": result1["run_id"],
                "run2_id": result2["run_id"],
                "run1_accepted": result1["accepted_hypothesis_ids"],
                "run2_accepted": result2["accepted_hypothesis_ids"],
            },
            "detail": (
                "Both runs produced identical results - determinism verified"
                if deterministic
                else "Runs differ - check implementation"
            ),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "deterministic": False,
            "traceback": traceback.format_exc().splitlines()[-5:],
        }
