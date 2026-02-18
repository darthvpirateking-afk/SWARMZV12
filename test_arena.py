"""
test_arena.py – Tests for ARENA v0.1 subsystem.

Covers: schema, scoring, store, engine, config, and API integration.
"""

import json
import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Schema Tests ────────────────────────────────────────────────────────

class TestArenaSchema:

    def test_arena_run_defaults(self):
        from swarmz_runtime.arena.schema import ArenaRun
        run = ArenaRun(id="test_1", prompt="hello", num_candidates=3)
        assert run.status.value == "pending"
        assert run.num_candidates == 3
        assert run.winner_id is None

    def test_arena_run_max_candidates(self):
        from swarmz_runtime.arena.schema import ArenaRun
        with pytest.raises(Exception):
            ArenaRun(id="test_2", prompt="hello", num_candidates=9)

    def test_arena_candidate_defaults(self):
        from swarmz_runtime.arena.schema import ArenaCandidate
        cand = ArenaCandidate(id="c1", run_id="r1", worker_index=0, prompt="p")
        assert cand.score == 0.0
        assert cand.rank == 0
        assert cand.status.value == "pending"

    def test_arena_config_defaults(self):
        from swarmz_runtime.arena.schema import ArenaConfig
        cfg = ArenaConfig()
        assert cfg.max_candidates == 8
        assert cfg.default_num_candidates == 3
        assert cfg.enabled is True


# ── Scoring Tests ───────────────────────────────────────────────────────

class TestArenaScoring:

    def test_score_empty_response(self):
        from swarmz_runtime.arena.scoring import score_candidate
        assert score_candidate("", "hello") == 0.0

    def test_score_length_only(self):
        from swarmz_runtime.arena.scoring import score_candidate
        s1 = score_candidate("short", "p", strategy="length_only")
        s2 = score_candidate("a" * 2000, "p", strategy="length_only")
        assert s1 < s2
        assert s2 == 1.0

    def test_score_length_quality(self):
        from swarmz_runtime.arena.scoring import score_candidate
        # Multi-line, prompt-relevant response should score higher
        short = score_candidate("yes", "explain testing")
        detailed = score_candidate(
            "Testing is important.\nIt verifies correctness.\n"
            "Explain the methodology for testing software.",
            "explain testing"
        )
        assert detailed > short

    def test_score_deterministic(self):
        from swarmz_runtime.arena.scoring import score_candidate
        s1 = score_candidate("hello world", "greet")
        s2 = score_candidate("hello world", "greet")
        assert s1 == s2

    def test_rank_candidates(self):
        from swarmz_runtime.arena.scoring import rank_candidates
        cands = [
            {"id": "c1", "score": 0.3, "worker_index": 0},
            {"id": "c2", "score": 0.8, "worker_index": 1},
            {"id": "c3", "score": 0.5, "worker_index": 2},
        ]
        ranked = rank_candidates(cands)
        assert ranked[0]["id"] == "c2"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["id"] == "c3"
        assert ranked[2]["id"] == "c1"

    def test_rank_tiebreaker(self):
        from swarmz_runtime.arena.scoring import rank_candidates
        cands = [
            {"id": "c1", "score": 0.5, "worker_index": 1},
            {"id": "c0", "score": 0.5, "worker_index": 0},
        ]
        ranked = rank_candidates(cands)
        # Tie-break: lower worker_index first
        assert ranked[0]["worker_index"] == 0


# ── Store Tests ─────────────────────────────────────────────────────────

class TestArenaStore:

    def test_save_and_load_run(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        store = ArenaStore(str(tmp_path))
        store.save_run({"id": "r1", "prompt": "test", "status": "pending"})
        runs = store.list_runs()
        assert len(runs) == 1
        assert runs[0]["id"] == "r1"

    def test_update_run(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        store = ArenaStore(str(tmp_path))
        store.save_run({"id": "r1", "prompt": "test", "status": "pending"})
        store.update_run("r1", {"status": "completed", "winner_id": "c1"})
        run = store.get_run("r1")
        assert run["status"] == "completed"
        assert run["winner_id"] == "c1"

    def test_save_and_get_candidate(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        store = ArenaStore(str(tmp_path))
        store.save_candidate({"id": "c1", "run_id": "r1", "score": 0.5})
        cands = store.get_candidates_for_run("r1")
        assert len(cands) == 1
        assert cands[0]["score"] == 0.5

    def test_missing_file_returns_empty(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        store = ArenaStore(str(tmp_path))
        assert store.list_runs() == []
        assert store.get_candidates_for_run("none") == []


# ── Config Tests ────────────────────────────────────────────────────────

class TestArenaConfig:

    def test_self_check_passes(self):
        from swarmz_runtime.arena.config import self_check
        ok, issues = self_check()
        assert ok is True
        assert issues == []

    def test_load_default_config(self):
        from swarmz_runtime.arena.config import load_config
        cfg = load_config()
        assert cfg.max_candidates == 8
        assert cfg.enabled is True


# ── Engine Tests ────────────────────────────────────────────────────────

class TestArenaEngine:

    def test_start_run(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        result = engine.start_run("Explain Python", num_candidates=3)
        assert result["status"] == "completed"
        assert result["winner_id"] is not None
        assert len(result["candidates"]) == 3

    def test_run_with_1_candidate(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        result = engine.start_run("Hello", num_candidates=1)
        assert result["status"] == "completed"
        assert len(result["candidates"]) == 1
        assert result["winner_id"] is not None

    def test_run_with_max_candidates(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        result = engine.start_run("Test", num_candidates=8)
        assert len(result["candidates"]) == 8

    def test_candidates_ranked_deterministically(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        r1 = engine.start_run("Same prompt", num_candidates=4)
        r2 = engine.start_run("Same prompt", num_candidates=4)
        # Same prompt and workers → same scores → same ranking
        scores1 = [c["score"] for c in r1["candidates"]]
        scores2 = [c["score"] for c in r2["candidates"]]
        assert scores1 == scores2

    def test_audit_integration(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        audit_log = []
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store, audit_fn=lambda e: audit_log.append(e))
        engine.start_run("Audit test", num_candidates=2)
        event_types = [e.event_type for e in audit_log]
        assert "ARENA_RUN_STARTED" in event_types
        assert "ARENA_RUN_COMPLETED" in event_types

    def test_get_run_details(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        result = engine.start_run("Detail test", num_candidates=2)
        details = engine.get_run(result["run_id"])
        assert details is not None
        assert "candidate_details" in details

    def test_list_runs(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        engine.start_run("Run 1", num_candidates=2)
        engine.start_run("Run 2", num_candidates=2)
        runs = engine.list_runs()
        assert len(runs) == 2

    def test_storage_persistence(self, tmp_path):
        from swarmz_runtime.arena.store import ArenaStore
        from swarmz_runtime.arena.engine import ArenaEngine
        store = ArenaStore(str(tmp_path))
        engine = ArenaEngine(store)
        result = engine.start_run("Persist test", num_candidates=2)

        # Verify files exist
        assert (tmp_path / "arena_runs.jsonl").exists()
        assert (tmp_path / "arena_candidates.jsonl").exists()

        # Reload from disk
        store2 = ArenaStore(str(tmp_path))
        runs = store2.list_runs()
        assert len(runs) == 1
        assert runs[0]["id"] == result["run_id"]


# ── API Tests (FastAPI TestClient) ──────────────────────────────────────

class TestArenaAPI:

    def _get_client(self):
        from fastapi.testclient import TestClient
        from swarmz_runtime.api.server import app
        return TestClient(app)

    def test_post_arena_run(self):
        client = self._get_client()
        resp = client.post("/v1/arena/run", json={
            "prompt": "Write a haiku about testing",
            "num_candidates": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["winner_id"] is not None
        assert len(data["candidates"]) == 3

    def test_list_arena_runs(self):
        client = self._get_client()
        resp = client.get("/v1/arena/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert "runs" in data
        assert "count" in data

    def test_get_arena_config(self):
        client = self._get_client()
        resp = client.get("/v1/arena/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "max_candidates" in data

    def test_arena_self_check(self):
        client = self._get_client()
        resp = client.get("/v1/arena/check")
        assert resp.status_code == 200
        data = resp.json()
        assert "ok" in data

    def test_arena_ui_page(self):
        client = self._get_client()
        resp = client.get("/arena")
        assert resp.status_code == 200
        assert "SWARMZ Arena" in resp.text

    def test_get_nonexistent_run(self):
        client = self._get_client()
        resp = client.get("/v1/arena/runs/nonexistent_id")
        assert resp.status_code == 404
