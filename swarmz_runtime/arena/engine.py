"""
arena/engine.py – ARENA v0.1 core engine.

Spawns up to 8 parallel workers, scores candidates deterministically,
selects a winner, and persists everything to JSONL storage + audit log.
"""

from __future__ import annotations

import uuid
import concurrent.futures
from datetime import datetime
from typing import Any, Dict, List, Optional

from swarmz_runtime.storage.schema import AuditEntry
from .schema import (
    ArenaRun,
    ArenaCandidate,
    ArenaRunStatus,
    CandidateStatus,
    ArenaConfig,
)
from .store import ArenaStore
from .scoring import score_candidate, rank_candidates
from .config import load_config


def _generate_response(prompt: str, worker_index: int) -> str:
    """Generate a candidate response for the given prompt.

    This is the pluggable generation function. For ARENA v0.1
    it produces deterministic synthetic responses.
    In production, this would call the model/sovereign dispatch.
    """
    # Deterministic synthetic response based on worker index
    base = f"Response from worker {worker_index} for: {prompt}"
    # Vary length and content deterministically per worker
    elaboration_lines = []
    words = prompt.split()
    for i in range(worker_index + 1):
        offset = i % max(len(words), 1)
        rotated = words[offset:] + words[:offset]
        elaboration_lines.append(f"Perspective {i + 1}: " + " ".join(rotated))
    detail = "\n".join(elaboration_lines)
    return f"{base}\n\n{detail}\n\nConclusion: This addresses the key aspects of the prompt from angle {worker_index}."


class ArenaEngine:
    """Orchestrates arena runs: spawn workers, score, rank, select winner."""

    def __init__(self, store: ArenaStore, audit_fn=None):
        self.store = store
        self._audit_fn = audit_fn  # callable(AuditEntry) to log audit

    def _audit(self, event_type: str, run_id: str, details: Dict[str, Any]):
        if self._audit_fn:
            entry = AuditEntry(
                event_type=event_type,
                mission_id=run_id,
                details=details,
            )
            try:
                self._audit_fn(entry)
            except Exception:
                pass  # best-effort audit

    def start_run(
        self,
        prompt: str,
        num_candidates: int = 3,
        scoring_strategy: str = "length_quality",
    ) -> Dict[str, Any]:
        """Start a new arena run.

        Spawns up to num_candidates parallel workers, scores results,
        ranks them, selects a winner, and persists everything.
        """
        config = load_config()
        num_candidates = min(num_candidates, config.max_candidates)
        if num_candidates < 1:
            num_candidates = 1

        run_id = f"arena_{uuid.uuid4().hex[:12]}"

        run = ArenaRun(
            id=run_id,
            prompt=prompt,
            num_candidates=num_candidates,
            scoring_strategy=scoring_strategy,
            status=ArenaRunStatus.RUNNING,
            config_snapshot=config.model_dump(mode="json"),
        )
        self.store.save_run(run.model_dump(mode="json"))
        self._audit(
            "ARENA_RUN_STARTED",
            run_id,
            {
                "prompt": prompt[:200],
                "num_candidates": num_candidates,
                "strategy": scoring_strategy,
            },
        )

        # Spawn parallel workers
        candidates = self._run_candidates(
            run_id, prompt, num_candidates, scoring_strategy
        )

        # Rank and select winner
        ranked = rank_candidates(candidates)
        winner_id = ranked[0]["id"] if ranked else None

        # Persist final state
        completed_at = datetime.now().isoformat()
        candidate_ids = [c["id"] for c in ranked]

        self.store.update_run(
            run_id,
            {
                "status": ArenaRunStatus.COMPLETED.value,
                "winner_id": winner_id,
                "candidates": candidate_ids,
                "completed_at": completed_at,
            },
        )

        self._audit(
            "ARENA_RUN_COMPLETED",
            run_id,
            {
                "winner_id": winner_id,
                "num_scored": len(ranked),
                "top_score": ranked[0]["score"] if ranked else 0,
            },
        )

        return {
            "run_id": run_id,
            "status": "completed",
            "winner_id": winner_id,
            "candidates": ranked,
            "completed_at": completed_at,
        }

    def _run_candidates(
        self, run_id: str, prompt: str, num_candidates: int, scoring_strategy: str
    ) -> List[Dict[str, Any]]:
        """Execute candidate generation in parallel."""
        results: List[Dict[str, Any]] = []

        # Use ThreadPoolExecutor for parallel execution (up to 8 workers)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(num_candidates, 8)
        ) as executor:
            futures = {}
            for i in range(num_candidates):
                cand_id = f"{run_id}_c{i}"
                candidate = ArenaCandidate(
                    id=cand_id,
                    run_id=run_id,
                    worker_index=i,
                    prompt=prompt,
                    status=CandidateStatus.RUNNING,
                    started_at=datetime.now(),
                )
                self.store.save_candidate(candidate.model_dump(mode="json"))
                future = executor.submit(_generate_response, prompt, i)
                futures[future] = (cand_id, i)

            for future in concurrent.futures.as_completed(futures):
                cand_id, worker_idx = futures[future]
                try:
                    response = future.result(timeout=30)
                    score = score_candidate(response, prompt, scoring_strategy)
                    self.store.update_candidate(
                        cand_id,
                        {
                            "response": response,
                            "score": score,
                            "status": CandidateStatus.SCORED.value,
                            "completed_at": datetime.now().isoformat(),
                        },
                    )
                    results.append(
                        {
                            "id": cand_id,
                            "run_id": run_id,
                            "worker_index": worker_idx,
                            "response": response,
                            "score": score,
                            "status": "scored",
                        }
                    )
                except Exception as e:
                    self.store.update_candidate(
                        cand_id,
                        {
                            "status": CandidateStatus.FAILED.value,
                            "error": str(e),
                            "completed_at": datetime.now().isoformat(),
                        },
                    )
                    results.append(
                        {
                            "id": cand_id,
                            "run_id": run_id,
                            "worker_index": worker_idx,
                            "response": "",
                            "score": 0.0,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        return results

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a run with its candidates."""
        run = self.store.get_run(run_id)
        if not run:
            return None
        run["candidate_details"] = self.store.get_candidates_for_run(run_id)
        return run

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent arena runs."""
        return self.store.list_runs(limit)
