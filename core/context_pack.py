# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/context_pack.py â€” Orchestrates all engines for mission lifecycle.

Provides:
  load()                  â†’ initialise all engines (singleton, lazy)
  before_mission(mission) â†’ gather context, select strategy, snapshot decision
  after_mission(mission, result, runtime_ms) â†’ update ALL engines
  daily_tick()            â†’ run daily scheduler tasks
  get_scoreboard()        â†’ readâ€‘only status for /v1/runtime/scoreboard

Engine wiring order (respects dependency graph):
  1. operator_anchor
  2. perf_ledger
  3. evolution_memory
  4. world_model
  5. divergence_engine
  6. entropy_monitor
  7. trajectory_engine
  8. counterfactual_engine
  9. relevance_engine
  10. phase_engine
  11. companion_master

Never crashes the caller â€” every engine call is wrapped in try/except.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.time_source import now

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# â”€â”€ Singleton engine instances â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_engines: Optional[Dict[str, Any]] = None
_loaded = False


def load() -> Dict[str, Any]:
    """Initialise all engines. Idempotent â€” returns cached instances."""
    global _engines, _loaded
    if _loaded and _engines:
        return _engines

    engines: Dict[str, Any] = {}

    # 1. operator_anchor
    try:
        from core.operator_anchor import load_or_create_anchor, verify_fingerprint

        anchor = load_or_create_anchor("data")
        read_only = not verify_fingerprint(anchor)
        engines["anchor"] = anchor
        engines["read_only"] = read_only
    except Exception:
        engines["anchor"] = {}
        engines["read_only"] = False

    # 2. perf_ledger
    try:
        from core.perf_ledger import PerfLedger

        engines["perf_ledger"] = PerfLedger("data")
    except Exception:
        engines["perf_ledger"] = None

    # 3. evolution_memory
    try:
        from core.evolution_memory import EvolutionMemory

        engines["evolution"] = EvolutionMemory(
            "data",
            anchor=engines.get("anchor"),
            read_only=engines.get("read_only", False),
        )
    except Exception:
        engines["evolution"] = None

    # 4. world_model
    try:
        from core.world_model import WorldModel

        engines["world_model"] = WorldModel("data")
    except Exception:
        engines["world_model"] = None

    # 5. divergence_engine
    try:
        from core.divergence_engine import DivergenceEngine

        engines["divergence"] = DivergenceEngine("data")
    except Exception:
        engines["divergence"] = None

    # 6. entropy_monitor
    try:
        from core.entropy_monitor import EntropyMonitor

        engines["entropy"] = EntropyMonitor("data")
    except Exception:
        engines["entropy"] = None

    # 7. trajectory_engine
    try:
        from core.trajectory_engine import TrajectoryEngine

        engines["trajectory"] = TrajectoryEngine(
            "data",
            engines.get("evolution"),
            engines.get("perf_ledger"),
            engines.get("world_model"),
            engines.get("divergence"),
            engines.get("entropy"),
        )
    except Exception:
        engines["trajectory"] = None

    # 8. counterfactual_engine
    try:
        from core.counterfactual_engine import CounterfactualEngine

        engines["counterfactual"] = CounterfactualEngine(
            "data",
            engines.get("evolution"),
            engines.get("trajectory"),
            engines.get("world_model"),
        )
    except Exception:
        engines["counterfactual"] = None

    # 9. relevance_engine
    try:
        from core.relevance_engine import RelevanceEngine

        engines["relevance"] = RelevanceEngine(
            "data",
            engines.get("evolution"),
            engines.get("counterfactual"),
        )
    except Exception:
        engines["relevance"] = None

    # 10. phase_engine
    try:
        from core.phase_engine import PhaseEngine

        engines["phase"] = PhaseEngine(
            "data",
            world_model=engines.get("world_model"),
            divergence=engines.get("divergence"),
            entropy=engines.get("entropy"),
            trajectory=engines.get("trajectory"),
        )
    except Exception:
        engines["phase"] = None

    # 11. companion_master
    try:
        from core.companion_master import ensure_master

        engines["companion_master"] = ensure_master()
    except Exception:
        engines["companion_master"] = None

    _engines = engines
    _loaded = True
    return engines


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


# â”€â”€ Beforeâ€‘mission hook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def before_mission(mission: Dict[str, Any]) -> Dict[str, Any]:
    """Gather context and select strategy before mission execution.

    Returns a context dict:
      strategy, candidates, inputs_hash, personality, attention_bundle, ...
    """
    eng = load()
    ctx: Dict[str, Any] = {"timestamp": now()}

    mission_id = mission.get("mission_id", "unknown")
    intent = mission.get("intent", mission.get("goal", "unknown"))
    inputs_hash = _hash(
        json.dumps({"id": mission_id, "intent": intent}, sort_keys=True)
    )
    ctx["inputs_hash"] = inputs_hash
    ctx["mission_id"] = mission_id

    # Personality vector
    try:
        evo = eng.get("evolution")
        if evo:
            ctx["personality"] = evo.get_personality()
        else:
            ctx["personality"] = {}
    except Exception:
        ctx["personality"] = {}

    # Strategy selection
    strategy = "baseline"
    candidates = []
    try:
        evo = eng.get("evolution")
        traj = eng.get("trajectory")
        if evo:
            candidates = evo.candidate_strategies(inputs_hash)
            bias_fn = None
            if traj:
                bias_fn = traj.strategy_bias
            strategy = evo.select_strategy(
                inputs_hash, default_strategy="baseline", bias_fn=bias_fn
            )
    except Exception:
        pass
    ctx["strategy"] = strategy
    ctx["candidates"] = candidates

    # Attention bundle (relevant memories)
    try:
        rel = eng.get("relevance")
        if rel:
            ctx["attention_bundle"] = rel.get_attention_bundle(limit=20)
        else:
            ctx["attention_bundle"] = []
    except Exception:
        ctx["attention_bundle"] = []

    # Counterfactual snapshot
    try:
        cf = eng.get("counterfactual")
        if cf:
            personality = ctx.get("personality", {})
            state_hash = ""
            try:
                sol = DATA_DIR / "state_of_life.json"
                if sol.exists():
                    state_hash = _hash(sol.read_text(encoding="utf-8"))
            except Exception:
                pass
            cf.record_snapshot(
                inputs_hash=inputs_hash,
                selected_strategy=strategy,
                candidate_strategies=candidates,
                expected_outcome_projection=0.5,
                state_of_life_hash=state_hash,
                personality_vector=personality,
            )
    except Exception:
        pass

    # AI audit
    try:
        from core.ai_audit import log_decision

        log_decision(
            decision_type="strategy_selection",
            mission_id=mission_id,
            strategy=strategy,
            inputs_hash=inputs_hash,
            rationale=f"Selected from {len(candidates)} candidates",
            confidence=ctx.get("personality", {}).get("risk_tolerance", 0.5),
            source="context_pack",
        )
    except Exception:
        pass

    return ctx


# â”€â”€ Afterâ€‘mission hook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def after_mission(
    mission: Dict[str, Any],
    result: Dict[str, Any],
    runtime_ms: int,
    *,
    strategy: str = "baseline",
    inputs_hash: str = "",
    candidates: Optional[list] = None,
) -> None:
    """Update ALL engines after mission completion.

    Called by the runner after each mission finishes.
    Every engine update is individually try/excepted â€” a failure in one
    engine must never block the others.
    """
    eng = load()
    if eng.get("read_only"):
        return  # fingerprint mismatch â€” no learning, no weight updates

    mission_id = mission.get("mission_id", "unknown")
    intent = mission.get("intent", mission.get("goal", "unknown"))
    success = result.get("ok", False)
    score = 1.0 if success else 0.0
    cost = result.get("cost_estimate", 0.0)
    if candidates is None:
        candidates = []

    # 1. perf_ledger
    try:
        pl = eng.get("perf_ledger")
        if pl:
            pl.append(mission_id, runtime_ms, success, cost)
    except Exception:
        pass

    # 2. evolution_memory
    try:
        evo = eng.get("evolution")
        if evo:
            evo.append_record(
                timestamp=now(),
                mission_type=intent,
                inputs_hash=inputs_hash,
                strategy_used=strategy,
                total_runtime_ms=runtime_ms,
                success_bool=success,
                cost_estimate=cost,
                score=score,
            )
            prev_avg = evo.strategy_average(strategy)
            evo.record_outcome(
                strategy, score, success, mission_id, inputs_hash, prev_avg, runtime_ms
            )
    except Exception:
        pass

    # 3. trajectory_engine (also triggers divergence, entropy, world_model internally)
    try:
        traj = eng.get("trajectory")
        if traj:
            traj.after_outcome(success, score, runtime_ms, strategy)
    except Exception:
        pass

    # 4. phase_engine
    try:
        phase = eng.get("phase")
        if phase:
            phase.after_outcome(success, score, runtime_ms, strategy)
    except Exception:
        pass

    # 5. counterfactual_engine
    try:
        cf = eng.get("counterfactual")
        if cf:
            trend = 0.0
            try:
                cs = DATA_DIR / "current_state.json"
                if cs.exists():
                    trend = json.loads(cs.read_text(encoding="utf-8")).get(
                        "recent_trend_vector", 0.0
                    )
            except Exception:
                pass
            cf.evaluate(
                mission_id=mission_id,
                inputs_hash=inputs_hash,
                selected_strategy=strategy,
                candidate_strategies=candidates,
                actual_score=score,
                success=success,
                trend_vector=trend,
            )
    except Exception:
        pass

    # 6. relevance_engine
    try:
        rel = eng.get("relevance")
        if rel:
            rel.after_outcome(
                mission_id, inputs_hash, strategy, score, success, runtime_ms
            )
    except Exception:
        pass

    # 7. companion_master
    try:
        from core.companion_master import record_mission_observed

        summary = result.get("plan_preview", result.get("note", ""))
        if isinstance(summary, str):
            summary = summary[:200]
        else:
            summary = str(summary)[:200]
        record_mission_observed(
            mission_id, intent, "SUCCESS" if success else "FAILURE", summary
        )
    except Exception:
        pass


# â”€â”€ Daily scheduler tick â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def daily_tick() -> Dict[str, Any]:
    """Run daily maintenance tasks.  Call once per day (or at startup if stale).

    Triggers: world_model recompute, phase report, daily brief, reflection,
    cognitive load, decision quality report.
    """
    eng = load()
    ran = []

    # world_model.recompute()
    try:
        wm = eng.get("world_model")
        if wm:
            wm.recompute()
            ran.append("world_model")
    except Exception:
        pass

    # trajectory â€” triggers daily_brief + reflection
    try:
        traj = eng.get("trajectory")
        if traj:
            traj.after_outcome(True, 0.5, 0, "daily_maintenance")
            ran.append("trajectory_daily")
    except Exception:
        pass

    # phase report
    try:
        phase = eng.get("phase")
        if phase:
            phase.after_outcome(True, 0.5, 0, "daily_maintenance")
            ran.append("phase_report")
    except Exception:
        pass

    # companion_master selfâ€‘assessment
    try:
        from core.companion_master import self_assessment

        assessment = self_assessment()
        ran.append("companion_selftest")
    except Exception:
        pass

    return {"ok": True, "ran": ran, "timestamp": now()}


# â”€â”€ Scoreboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def get_scoreboard() -> Dict[str, Any]:
    """Readâ€‘only status for /v1/runtime/scoreboard.

    Aggregates status from all engines.
    """
    eng = load()
    board: Dict[str, Any] = {"timestamp": now()}

    # personality
    try:
        evo = eng.get("evolution")
        if evo:
            board["personality"] = evo.get_personality()
            board["companion_state"] = evo.get_companion_state()
            sb = evo.get_scoreboard()
            board["evolution_scoreboard"] = sb
    except Exception:
        board["personality"] = {}
        board["companion_state"] = {}

    # read_only
    board["read_only"] = eng.get("read_only", False)

    # trajectory
    try:
        cs = DATA_DIR / "current_state.json"
        if cs.exists():
            board["current_state"] = json.loads(cs.read_text(encoding="utf-8"))
    except Exception:
        pass

    try:
        fs = DATA_DIR / "future_state.json"
        if fs.exists():
            board["future_state"] = json.loads(fs.read_text(encoding="utf-8"))
    except Exception:
        pass

    # phase
    try:
        pr = DATA_DIR / "phase_report.txt"
        if pr.exists():
            board["phase_report"] = pr.read_text(encoding="utf-8")[:500]
    except Exception:
        pass

    # entropy mode
    try:
        ent = eng.get("entropy")
        if ent:
            board["entropy_mode"] = ent._compute_metrics().get("mode", "unknown")
    except Exception:
        pass

    # pending prepared actions
    try:
        from core.safe_execution import count_pending

        board["pending_actions"] = count_pending()
    except Exception:
        pass

    return board
