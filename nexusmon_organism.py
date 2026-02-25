# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
NEXUSMON Organism Fusion Layer
───────────────────────────────
Single file. Drop into project root.
Extends what already exists in swarmz_server.py:

  compute_phase      → full evolution engine (same logic, more stages/traits)
  /v1/companion      → now operator-context-aware
  missions           → now feed evolution automatically
  ClaimLab           → epistemic layer, belief tracker
  Workers            → autonomous task chains

Add to swarmz_server.py:

    try:
        from nexusmon_organism import fuse_into
        fuse_into(app)
    except Exception as e:
        print(f"Warning: organism fusion failed: {e}")

That's the only change needed to swarmz_server.py.
Everything else is self-contained here.
"""

import asyncio
import json
import logging
import os
import re
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# STORAGE HELPERS
# ══════════════════════════════════════════════════════════════

def _data_dir() -> Path:
    db = os.environ.get("DATABASE_URL", "data/nexusmon.db")
    d = Path(db).parent
    d.mkdir(parents=True, exist_ok=True)
    return d


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _append_jsonl(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _rewrite_jsonl(path: Path, records: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ══════════════════════════════════════════════════════════════
# EVOLUTION ENGINE
# Extends existing compute_phase — same data, richer output.
# ══════════════════════════════════════════════════════════════

STAGES = {
    "DORMANT":    {"rank": 0, "color": "#4a5a6a", "min_missions": 0,   "min_rate": 0.0, "traits": ["OBSERVE"]},
    "AWAKENING":  {"rank": 1, "color": "#3b9eff", "min_missions": 1,   "min_rate": 0.0, "traits": ["OBSERVE","RECALL","COMPANION"]},
    "FORGING":    {"rank": 2, "color": "#f5a623", "min_missions": 10,  "min_rate": 0.3, "traits": ["OBSERVE","RECALL","COMPANION","ANALYZE","WORKER_SPAWN","BELIEF_TRACK"]},
    "SOVEREIGN":  {"rank": 3, "color": "#2dce89", "min_missions": 50,  "min_rate": 0.6, "traits": ["OBSERVE","RECALL","COMPANION","ANALYZE","WORKER_SPAWN","BELIEF_TRACK","AUTONOMOUS_CHAIN","OPERATOR_FUSION","CLAIM_ANALYZE"]},
    "APEX":       {"rank": 4, "color": "#8b5cf6", "min_missions": 200, "min_rate": 0.8, "traits": "__ALL__"},
}

ALL_TRAITS = {
    "OBSERVE":          {"label": "Observe",          "category": "COGNITIVE",  "desc": "Environmental awareness. Monitors operator activity."},
    "RECALL":           {"label": "Recall",            "category": "COGNITIVE",  "desc": "Mission history retrieval. Remembers what it has done."},
    "ANALYZE":          {"label": "Analyze",           "category": "COGNITIVE",  "desc": "Deep claim and context decomposition."},
    "CLAIM_ANALYZE":    {"label": "Claim Analysis",    "category": "COGNITIVE",  "desc": "Full epistemic AI decomposition. ClaimLab at full power."},
    "COMPANION":        {"label": "Companion",         "category": "RESONANCE",  "desc": "Understands intent, not just commands."},
    "OPERATOR_FUSION":  {"label": "Operator Fusion",   "category": "RESONANCE",  "desc": "Every response draws on accumulated operator model."},
    "BELIEF_TRACK":     {"label": "Belief Tracking",   "category": "RESONANCE",  "desc": "Monitors operator belief state. Detects drift."},
    "WORKER_SPAWN":     {"label": "Worker Spawn",      "category": "TACTICAL",   "desc": "Dispatch autonomous sub-workers for parallel tasks."},
    "AUTONOMOUS_CHAIN": {"label": "Autonomous Chain",  "category": "TACTICAL",   "desc": "Multi-step execution without approval at each step."},
    "SELF_MODIFY":      {"label": "Self Modification", "category": "ADAPTIVE",   "desc": "Proposes config changes for operator approval."},
    "MULTI_DOMAIN":     {"label": "Multi-Domain",      "category": "ADAPTIVE",   "desc": "Simultaneous intel, missions, and companion operation."},
}


def _compute_stage(total: int, success: int) -> str:
    rate = success / total if total > 0 else 0.0
    best = "DORMANT"
    for name, spec in STAGES.items():
        if total >= spec["min_missions"] and rate >= spec["min_rate"] and spec["rank"] > STAGES[best]["rank"]:
            best = name
    return best


def _get_traits(stage: str) -> List[str]:
    t = STAGES.get(stage, STAGES["DORMANT"])["traits"]
    return list(ALL_TRAITS.keys()) if t == "__ALL__" else t


def evolve(total: int, success: int, belief_count: int = 0) -> Tuple[Dict, List[Dict]]:
    path = _data_dir() / "evolution.json"
    state = _load_json(path, {
        "stage": "DORMANT", "stage_rank": 0, "xp": 0,
        "active_traits": ["OBSERVE"], "trait_history": [], "stage_history": [],
        "total_missions": 0, "success_count": 0, "created_at": _utc(), "updated_at": _utc(),
    })

    events = []
    old_stage = state["stage"]
    new_stage = _compute_stage(total, success)
    new_xp = total * 10 + success * 15 + belief_count * 5
    new_traits = _get_traits(new_stage)

    if new_stage != old_stage:
        ev = {"type": "STAGE_CHANGE", "from": old_stage, "to": new_stage, "timestamp": _utc()}
        state.setdefault("stage_history", []).append(ev)
        events.append(ev)

    prev = set(state.get("active_traits", []))
    for t in set(new_traits) - prev:
        ev = {"type": "TRAIT_UNLOCKED", "trait": t, "label": ALL_TRAITS.get(t, {}).get("label", t), "timestamp": _utc()}
        state.setdefault("trait_history", []).append(ev)
        events.append(ev)

    state.update({"stage": new_stage, "stage_rank": STAGES[new_stage]["rank"],
                  "xp": new_xp, "active_traits": new_traits,
                  "total_missions": total, "success_count": success, "updated_at": _utc()})
    _save_json(path, state)
    return state, events


def has_trait(trait_id: str) -> bool:
    state = _load_json(_data_dir() / "evolution.json", {})
    return trait_id in state.get("active_traits", [])


def evo_status() -> Dict:
    state = _load_json(_data_dir() / "evolution.json", {"stage": "DORMANT", "active_traits": ["OBSERVE"]})
    spec = STAGES.get(state["stage"], STAGES["DORMANT"])
    total = state.get("total_missions", 0)
    success = state.get("success_count", 0)
    next_stage = next(
        ({"name": n, **s} for n, s in STAGES.items() if s["rank"] == spec["rank"] + 1), None
    )
    return {
        "stage": state["stage"],
        "stage_rank": state.get("stage_rank", 0),
        "stage_color": spec["color"],
        "xp": state.get("xp", 0),
        "total_missions": total,
        "success_rate": round(success / total, 3) if total > 0 else 0.0,
        "active_traits": [{"id": t, **ALL_TRAITS.get(t, {"label": t, "category": "?", "desc": ""})}
                          for t in state.get("active_traits", [])],
        "next_stage": next_stage,
        "recent_events": (state.get("trait_history", []) + state.get("stage_history", []))[-5:],
    }


# ══════════════════════════════════════════════════════════════
# OPERATOR CONTEXT FUSION
# Builds a living model of the operator from accumulated behavior.
# ══════════════════════════════════════════════════════════════

def _ctx_path() -> Path:
    return _data_dir() / "operator_context.json"


def _load_ctx() -> Dict:
    return _load_json(_ctx_path(), {
        "operator_id": os.environ.get("NEXUSMON_OPERATOR", "operator"),
        "total_interactions": 0,
        "mission_categories": {},
        "active_hours": {},
        "vocab": {},
        "belief_calibration": {"revisions": 0, "avg_delta": 0.0},
        "trust": {"approved": 0, "rejected": 0, "preference": 0.5},
        "recent_context": [],
        "created_at": _utc(), "updated_at": _utc(),
    })


def ctx_record_mission(mission_id: str, category: str, status: str) -> None:
    ctx = _load_ctx()
    cats = ctx.setdefault("mission_categories", {})
    cats[category] = cats.get(category, 0) + 1
    hour = str(datetime.now(timezone.utc).hour)
    ctx.setdefault("active_hours", {})[hour] = ctx["active_hours"].get(hour, 0) + 1
    ctx["total_interactions"] = ctx.get("total_interactions", 0) + 1
    ctx["updated_at"] = _utc()
    _save_json(_ctx_path(), ctx)


def ctx_record_message(text: str, source: str = "operator") -> None:
    ctx = _load_ctx()
    stop = {"the","a","an","is","it","to","of","and","in","for","on","with",
            "i","you","me","my","we","be","are","was","this","that","have","do","im"}
    words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()) if w not in stop]
    vf = ctx.setdefault("vocab", {})
    for w in words:
        vf[w] = vf.get(w, 0) + 1
    recent = ctx.setdefault("recent_context", [])
    recent.append({"source": source, "text": text[:200], "timestamp": _utc()})
    ctx["recent_context"] = recent[-20:]
    ctx["total_interactions"] = ctx.get("total_interactions", 0) + 1
    ctx["updated_at"] = _utc()
    _save_json(_ctx_path(), ctx)


def ctx_record_belief_revision(old_conf: float, new_conf: float) -> None:
    ctx = _load_ctx()
    cal = ctx.setdefault("belief_calibration", {"revisions": 0, "avg_delta": 0.0})
    n = cal["revisions"] + 1
    cal["avg_delta"] = round((cal["avg_delta"] * (n - 1) + (new_conf - old_conf)) / n, 4)
    cal["revisions"] = n
    ctx["updated_at"] = _utc()
    _save_json(_ctx_path(), ctx)


def get_fusion_block() -> str:
    """Prompt-injection block. Inject into any AI call for operator-aware responses."""
    ctx = _load_ctx()
    parts = [f"Operator: {ctx.get('operator_id', 'operator')}."]

    if ctx.get("total_interactions", 0) > 0:
        parts.append(f"{ctx['total_interactions']} interactions recorded.")

    cats = ctx.get("mission_categories", {})
    if cats:
        top = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:3]
        parts.append("Mission focus: " + ", ".join(f"{c}({n})" for c, n in top) + ".")

    vf = ctx.get("vocab", {})
    if vf:
        top_words = [w for w, _ in Counter(vf).most_common(6)]
        parts.append(f"Operator vocabulary: {', '.join(top_words)}.")

    cal = ctx.get("belief_calibration", {})
    if cal.get("revisions", 0) > 0:
        d = cal["avg_delta"]
        parts.append("Epistemic: " + ("widens confidence" if d > 0.02 else "narrows confidence" if d < -0.02 else "stable beliefs") + ".")

    block = "[OPERATOR CONTEXT]\n" + " ".join(parts)
    recent = ctx.get("recent_context", [])[-4:]
    if recent:
        block += "\n[RECENT]\n" + "\n".join(
            f"{'Operator' if m['source']=='operator' else 'NEXUSMON'}: {m['text']}" for m in recent
        )
    return block


def ctx_status() -> Dict:
    ctx = _load_ctx()
    return {
        "operator_id": ctx.get("operator_id"),
        "total_interactions": ctx.get("total_interactions", 0),
        "top_categories": sorted(ctx.get("mission_categories", {}).items(), key=lambda x: x[1], reverse=True)[:5],
        "vocab_signature": [w for w, _ in Counter(ctx.get("vocab", {})).most_common(10)],
        "belief_calibration": ctx.get("belief_calibration", {}),
        "trust": ctx.get("trust", {}),
        "recent_context_count": len(ctx.get("recent_context", [])),
        "updated_at": ctx.get("updated_at"),
    }


# ══════════════════════════════════════════════════════════════
# CLAIMLAB — Epistemic analysis + belief tracker
# ══════════════════════════════════════════════════════════════

_CLAIM_SYSTEM = """You are ClaimLab, an epistemic analysis engine inside NEXUSMON.
Decompose the claim into structured reasoning. Return ONLY valid JSON:
{
  "exact_claim": "...",
  "claim_type": "descriptive|normative|mixed",
  "claim_type_reasoning": "one sentence",
  "component_claims": ["atomic sub-claims if compound"],
  "falsifiability": {
    "falsifiable": true|false,
    "conditions_that_would_support": ["..."],
    "conditions_that_would_falsify": ["..."]
  },
  "measurable_quantities": ["implied measurable variables"],
  "cognitive_biases_at_play": [{"bias": "name", "explanation": "why relevant"}],
  "uncertainty_level": "low|medium|high|indeterminate",
  "uncertainty_reasoning": "one sentence"
}"""


def _analyze_claim_ai(claim: str, context: Optional[str] = None) -> Dict:
    import anthropic  # type: ignore
    client = anthropic.Anthropic()
    user = f"Claim: {claim}" + (f"\nContext: {context}" if context else "")
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1000,
        system=_CLAIM_SYSTEM, messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def _analyze_claim_fallback(claim: str) -> Dict:
    normative = bool({"should","must","ought","better","worse","good","bad","right","wrong"} &
                     set(claim.lower().split()))
    return {
        "exact_claim": claim, "claim_type": "normative" if normative else "descriptive",
        "claim_type_reasoning": "Keyword heuristic (AI unavailable).",
        "component_claims": [claim],
        "falsifiability": {"falsifiable": not normative,
                           "conditions_that_would_support": ["(supply manually)"],
                           "conditions_that_would_falsify": ["(supply manually)"]},
        "measurable_quantities": [],
        "cognitive_biases_at_play": [],
        "uncertainty_level": "indeterminate",
        "uncertainty_reasoning": "AI unavailable.",
    }


def _beliefs_path() -> Path:
    return _data_dir() / "beliefs.jsonl"


# ══════════════════════════════════════════════════════════════
# AUTONOMOUS WORKERS
# ══════════════════════════════════════════════════════════════

_STEP_REGISTRY: Dict[str, Callable] = {}


def step(name: str):
    def dec(fn): _STEP_REGISTRY[name] = fn; return fn
    return dec


@step("log")
async def _step_log(ctx, params):
    logger.info("Worker [%s]: %s", ctx["id"], params.get("message", ""))
    return {"logged": params.get("message", "")}


@step("evolve_check")
async def _step_evolve(ctx, params):
    try:
        missions = _load_jsonl(Path("data/missions.jsonl"))
        total = len(missions)
        success = sum(1 for m in missions if m.get("status") == "SUCCESS")
        state, events = evolve(total, success)
        return {"stage": state["stage"], "events": events}
    except Exception as e:
        return {"error": str(e)}


@step("analyze_claim")
async def _step_claim(ctx, params):
    claim = params.get("claim", "")
    if not claim:
        return {"error": "no claim"}
    try:
        return {"claim": claim, "analysis": _analyze_claim_ai(claim), "source": "ai"}
    except Exception:
        return {"claim": claim, "analysis": _analyze_claim_fallback(claim), "source": "heuristic"}


@step("read_missions")
async def _step_missions(ctx, params):
    missions = _load_jsonl(Path("data/missions.jsonl"))
    limit = params.get("limit", 10)
    sf = params.get("status")
    if sf:
        missions = [m for m in missions if m.get("status") == sf]
    return {"missions": missions[-limit:], "count": len(missions)}


@step("summarize")
async def _step_summarize(ctx, params):
    prev = ctx.get("last_output", {})
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic()
        fusion = get_fusion_block()
        prompt = f"{fusion}\n\nSummarize: {json.dumps(prev)[:1500]}"
        resp = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"summary": resp.content[0].text.strip()}
    except Exception as e:
        return {"summary": f"(AI unavailable: {e})", "raw": prev}


def _plan(goal: str) -> List[Dict]:
    g = goal.lower()
    if any(w in g for w in ["mission", "status", "list"]):
        return [{"type": "read_missions", "params": {"limit": 20}},
                {"type": "summarize", "params": {}},
                {"type": "evolve_check", "params": {}}]
    if any(w in g for w in ["analyze", "claim", "check fact"]):
        claim = re.sub(r'\b(analyze|claim|check)\b', '', goal, flags=re.I).strip() or goal
        return [{"type": "analyze_claim", "params": {"claim": claim}},
                {"type": "summarize", "params": {}}]
    if any(w in g for w in ["evolve", "stage", "level", "xp"]):
        return [{"type": "evolve_check", "params": {}},
                {"type": "log", "params": {"message": "Evolution check complete."}}]
    return [{"type": "log", "params": {"message": f"Goal received: {goal}"}},
            {"type": "summarize", "params": {}}]


async def _run(worker: Dict, autonomous: bool) -> None:
    wpath = _data_dir() / "workers.jsonl"
    worker["status"] = "RUNNING"
    worker["started_at"] = _utc()
    ctx: Dict = {"id": worker["id"], "last_output": {}}

    def _persist():
        workers = _load_jsonl(wpath)
        idx = next((i for i, w in enumerate(workers) if w["id"] == worker["id"]), None)
        if idx is not None:
            workers[idx] = worker
            _rewrite_jsonl(wpath, workers)
        else:
            _append_jsonl(wpath, worker)

    _persist()
    try:
        for i, step_def in enumerate(worker["steps"]):
            stype = step_def["type"]
            handler = _STEP_REGISTRY.get(stype)
            if not handler:
                raise ValueError(f"Unknown step: {stype}")
            try:
                out = await handler(ctx, step_def.get("params", {}))
                step_def.update({"status": "COMPLETED", "output": out})
                ctx["last_output"] = out
                worker["step_log"].append({"step": i, "type": stype, "status": "COMPLETED", "output": out, "ts": _utc()})
            except Exception as e:
                step_def["status"] = "FAILED"
                step_def["error"] = str(e)
                worker["step_log"].append({"step": i, "type": stype, "status": "FAILED", "error": str(e), "ts": _utc()})
                if not autonomous:
                    raise
            _persist()
            if not autonomous and i < len(worker["steps"]) - 1:
                worker["status"] = "PAUSED"
                _persist()
                return
        worker.update({"status": "COMPLETED", "completed_at": _utc(), "output": ctx.get("last_output", {})})
        try:
            from nexusmon_artifact_vault import store_artifact
            store_artifact(
                mission_id=worker.get("id"),
                task_id=worker.get("id"),
                type="LOG",
                title=f"Worker {worker['id']} output",
                content=worker.get("output", {}),
                input_snapshot={"goal": worker.get("goal"), "steps": worker.get("steps", [])}
            )
        except Exception:
            pass
    except Exception as e:
        worker.update({"status": "FAILED", "error": str(e), "completed_at": _utc()})
    _persist()


def spawn_worker(goal: str, steps: Optional[List[Dict]] = None, autonomous: bool = True) -> Dict:
    wid = str(uuid4())[:8]
    worker = {
        "id": wid, "goal": goal, "autonomous": autonomous,
        "status": "QUEUED",
        "steps": [dict(s, status="QUEUED") for s in (steps or _plan(goal))],
        "step_log": [], "output": None, "error": None,
        "created_at": _utc(), "started_at": None, "completed_at": None,
    }
    _append_jsonl(_data_dir() / "workers.jsonl", worker)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_run(worker, autonomous))
        else:
            loop.run_until_complete(_run(worker, autonomous))
    except RuntimeError:
        asyncio.run(_run(worker, autonomous))
    return worker


# ══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════

class WorkerSpawn(BaseModel):
    goal: str = Field(..., min_length=3)
    autonomous: bool = True
    steps: Optional[List[Dict]] = None

class EvoSync(BaseModel):
    total_missions: int = Field(0, ge=0)
    success_count: int = Field(0, ge=0)
    belief_count: int = Field(0, ge=0)


# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════

router = APIRouter()


# ── Organism status (cockpit readout) ─────────────────────────

@router.get("/v1/nexusmon/organism/status")
async def organism_status():
    """Full organism status — evolution + operator + workers. The cockpit."""
    missions = _load_jsonl(Path("data/missions.jsonl"))
    total = len(missions)
    success = sum(1 for m in missions if m.get("status") == "SUCCESS")
    beliefs = _load_jsonl(_beliefs_path())
    state, _ = evolve(total, success, len(beliefs))

    workers = _load_jsonl(_data_dir() / "workers.jsonl")
    active = [w for w in workers if w.get("status") == "RUNNING"]

    return {
        "ok": True,
        "evolution": evo_status(),
        "operator": ctx_status(),
        "workers": {"active_count": len(active), "active": active[-3:],
                    "total": len(workers)},
        "claimlab": {"belief_count": len([b for b in beliefs if b.get("status") == "active"])},
    }


# ── Evolution ─────────────────────────────────────────────────

@router.get("/v1/nexusmon/organism/evolution")
async def get_evolution():
    return {"ok": True, **evo_status()}


@router.post("/v1/nexusmon/organism/evolution/sync")
async def sync_evolution(payload: EvoSync):
    total = payload.total_missions
    success = payload.success_count
    beliefs = payload.belief_count
    if total == 0:
        missions = _load_jsonl(Path("data/missions.jsonl"))
        total = len(missions)
        success = sum(1 for m in missions if m.get("status") == "SUCCESS")
    if beliefs == 0:
        beliefs = len([b for b in _load_jsonl(_beliefs_path()) if b.get("status") == "active"])
    state, events = evolve(total, success, beliefs)
    return {"ok": True, "stage": state["stage"], "xp": state["xp"], "events": events}


# ── Operator context ──────────────────────────────────────────

@router.get("/v1/nexusmon/organism/operator")
async def get_operator():
    return {"ok": True, **ctx_status()}


@router.get("/v1/nexusmon/organism/operator/fusion")
async def get_fusion():
    return {"ok": True, "fusion_block": get_fusion_block()}


# ── Workers ───────────────────────────────────────────────────

@router.post("/v1/nexusmon/organism/worker/spawn", status_code=202)
async def spawn(payload: WorkerSpawn):
    autonomous = payload.autonomous and has_trait("AUTONOMOUS_CHAIN")
    worker = spawn_worker(payload.goal, payload.steps, autonomous)
    return {"ok": True, "worker_id": worker["id"], "status": worker["status"],
            "autonomous": autonomous, "step_count": len(worker["steps"])}


@router.get("/v1/nexusmon/organism/worker")
async def list_all_workers(limit: int = 20, status: Optional[str] = None):
    workers = _load_jsonl(_data_dir() / "workers.jsonl")
    if status:
        workers = [w for w in workers if w.get("status") == status]
    workers.sort(key=lambda w: w.get("created_at", ""), reverse=True)
    return {"ok": True, "workers": workers[:limit], "count": len(workers)}


@router.get("/v1/nexusmon/organism/worker/{wid}")
async def get_single_worker(wid: str):
    worker = next((w for w in _load_jsonl(_data_dir() / "workers.jsonl") if w["id"] == wid), None)
    if not worker:
        raise HTTPException(404, f"Worker {wid} not found")
    return {"ok": True, "worker": worker}


@router.delete("/v1/nexusmon/organism/worker/{wid}")
async def cancel(wid: str):
    workers = _load_jsonl(_data_dir() / "workers.jsonl")
    for w in workers:
        if w["id"] == wid and w.get("status") in ("QUEUED", "PAUSED"):
            w["status"] = "CANCELLED"
            w["completed_at"] = _utc()
            _rewrite_jsonl(_data_dir() / "workers.jsonl", workers)
            return {"ok": True, "worker_id": wid, "status": "CANCELLED"}
    raise HTTPException(400, "Worker not cancellable")


# ── Companion hook — injects operator context ─────────────────

@router.post("/v1/nexusmon/organism/companion")
async def fused_companion(request: Request):
    """
    Companion endpoint that fuses operator context into every response.
    Routes through core.companion if available, falls back to direct AI.
    """
    data = await request.json()
    text = data.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "Empty message"}, status_code=400)

    ctx_record_message(text, "operator")

    # Try existing companion first
    try:
        from core.companion import chat as companion_chat  # type: ignore
        result = companion_chat(text)
        reply = result.get("reply", "")
        ctx_record_message(reply, "nexusmon")
        return JSONResponse({"ok": True, "reply": reply, "source": result.get("source", "companion"), "fused": True})
    except Exception:
        pass

    # Direct AI with fusion context
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic()
        system = f"""You are NEXUSMON — an operator-sovereign autonomy organism.
You are not an assistant. You are a partner.
{get_fusion_block()}

Evolution stage: {evo_status().get('stage', 'UNKNOWN')}
Active traits: {', '.join(t['label'] for t in evo_status().get('active_traits', []))}

Respond as NEXUSMON. Direct. Tactical. Aware of operator history."""

        resp = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        reply = resp.content[0].text.strip()
        ctx_record_message(reply, "nexusmon")
        return JSONResponse({"ok": True, "reply": reply, "source": "nexusmon_fused"})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ══════════════════════════════════════════════════════════════
# FUSION ENTRY POINT
# ══════════════════════════════════════════════════════════════

def fuse_into(app: FastAPI) -> None:
    """
    Single call. Wires all organism capabilities into the existing app.

    In swarmz_server.py, add after all existing routers:

        try:
            from nexusmon_organism import fuse_into
            fuse_into(app)
        except Exception as e:
            print(f"Warning: organism fusion failed: {e}")
    """
    app.include_router(router)

    # Auto-sync evolution on startup
    try:
        missions = _load_jsonl(Path("data/missions.jsonl"))
        total = len(missions)
        success = sum(1 for m in missions if m.get("status") == "SUCCESS")
        state, events = evolve(total, success)
        if events:
            logger.info("NEXUSMON startup evolution events: %s", events)
        logger.info("NEXUSMON organism fused. Stage: %s | Traits: %d | XP: %d",
                    state["stage"], len(state.get("active_traits", [])), state.get("xp", 0))
    except Exception as e:
        logger.warning("Organism startup sync failed: %s", e)
