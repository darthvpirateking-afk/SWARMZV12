"""
NEXUSMON Cognitive Instrumentation Layer
════════════════════════════════════════
Full implementation of all cognitive measurement systems.
Extends ClaimLab. Integrates with organism evolution.

Systems:
  1. Prediction Tracker       — Brier-scored forecasts + calibration curves
  2. Belief Dependency Graph  — belief networks, cascade updates
  3. Argument Compiler        — premises → inference → conclusion validator
  4. Counter-Argument Engine  — strongest opposing model generator
  5. Decision Autopsy         — outcome classification matrix
  6. Counterfactual Diary     — alternative outcome recorder
  7. Error Taxonomy Logger    — failure pattern classifier
  8. Abstraction Ladder       — 5-level concept elevator
  9. Concept Dependency Graph — prerequisite mapper
 10. Causality Sandbox        — DAG builder + intervention simulator
 11. Source Reliability Map   — longitudinal source scoring
 12. Attention Audit          — focus quality tracker
 13. Memory Distortion Logger — recall vs reality measurement
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# ── Storage helpers (mirrors nexusmon_organism pattern) ────────

def _data_dir() -> Path:
    db = os.environ.get("DATABASE_URL", "data/nexusmon.db")
    d = Path(db).parent
    d.mkdir(parents=True, exist_ok=True)
    return d


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _uid() -> str:
    return str(uuid4())[:8]


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
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ai(system: str, user: str, max_tokens: int = 800) -> str:
    import anthropic

    client = anthropic.Anthropic()
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return r.content[0].text.strip()


def _ai_json(system: str, user: str, max_tokens: int = 1000) -> Dict:
    raw = _ai(system + "\n\nReturn ONLY valid JSON. No markdown.", user, max_tokens)
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[len("```json") :].strip()
    if raw.startswith("```"):
        raw = raw[len("```") :].strip()
    if raw.endswith("```"):
        raw = raw[: -len("```")].strip()
    return json.loads(raw)


# ══════════════════════════════════════════════════════════════
# 1. PREDICTION TRACKER
# ══════════════════════════════════════════════════════════════

_PRED_PATH = lambda: _data_dir() / "predictions.jsonl"


def brier_score(p: float, outcome: bool) -> float:
    return round((p - (1.0 if outcome else 0.0)) ** 2, 4)


def calibration_buckets(predictions: List[Dict]) -> List[Dict]:
    resolved = [
        p for p in predictions if p.get("resolved") and p.get("outcome") is not None
    ]
    buckets: Dict[int, List] = defaultdict(list)
    for p in resolved:
        bucket = min(9, int(p["probability"] * 10))
        buckets[bucket].append(1 if p["outcome"] else 0)
    result = []
    for i in range(10):
        items = buckets.get(i, [])
        result.append(
            {
                "bucket": f"{i*10}-{i*10+9}%",
                "predicted_prob": i * 0.1 + 0.05,
                "actual_rate": round(sum(items) / len(items), 3) if items else None,
                "count": len(items),
            }
        )
    return result


def avg_brier(predictions: List[Dict]) -> Optional[float]:
    resolved = [p for p in predictions if p.get("brier_score") is not None]
    if not resolved:
        return None
    return round(sum(p["brier_score"] for p in resolved) / len(resolved), 4)


# ══════════════════════════════════════════════════════════════
# 2. BELIEF DEPENDENCY GRAPH
# ══════════════════════════════════════════════════════════════

_BDG_PATH = lambda: _data_dir() / "belief_graph.json"


def _load_graph() -> Dict:
    return _load_json(_BDG_PATH(), {"nodes": {}, "edges": []})


def _save_graph(g: Dict) -> None:
    _save_json(_BDG_PATH(), g)


def bdg_add_node(belief_id: str, claim: str, confidence: float) -> None:
    g = _load_graph()
    g["nodes"][belief_id] = {
        "id": belief_id,
        "claim": claim,
        "confidence": confidence,
        "updated_at": _utc(),
    }
    _save_graph(g)


def bdg_add_dependency(from_id: str, to_id: str, strength: float = 1.0) -> None:
    g = _load_graph()
    edge = {"from": from_id, "to": to_id, "strength": strength, "created_at": _utc()}
    if edge not in g["edges"]:
        g["edges"].append(edge)
    _save_graph(g)


def bdg_cascade(weakened_id: str, old_conf: float, new_conf: float) -> List[Dict]:
    g = _load_graph()
    delta = new_conf - old_conf
    affected = []
    for edge in g["edges"]:
        if edge["to"] == weakened_id:
            dep = g["nodes"].get(edge["from"])
            if dep:
                implied_delta = delta * edge["strength"]
                affected.append(
                    {
                        "belief_id": dep["id"],
                        "claim": dep["claim"],
                        "current_confidence": dep["confidence"],
                        "implied_delta": round(implied_delta, 4),
                        "suggested_confidence": round(
                            max(0.0, min(1.0, dep["confidence"] + implied_delta)), 3
                        ),
                        "reason": f"Upstream belief '{g['nodes'].get(weakened_id, {}).get('claim','?')[:60]}' changed by {delta:+.2f}",
                    }
                )
    return affected


# ══════════════════════════════════════════════════════════════
# 3. ARGUMENT COMPILER
# ══════════════════════════════════════════════════════════════

_ARG_SYSTEM = """You are a formal argument compiler. Analyze the argument and return JSON:
{
  "premises": [{"id": "P1", "statement": "...", "type": "empirical|normative|definitional", "verifiable": true}],
  "inference_type": "deductive|inductive|abductive|analogical",
  "inference_validity": "valid|invalid|uncertain",
  "conclusion": "...",
  "logical_gaps": ["any missing steps"],
  "hidden_assumptions": ["unstated premises required for the inference to hold"],
  "strength": "strong|moderate|weak",
  "strength_reasoning": "one sentence"
}"""


def compile_argument(text: str) -> Dict:
    try:
        return _ai_json(_ARG_SYSTEM, f"Argument: {text}")
    except Exception:
        return {
            "error": "AI unavailable",
            "raw": text,
            "premises": [],
            "conclusion": text,
            "inference_validity": "unknown",
            "strength": "unknown",
        }


# ══════════════════════════════════════════════════════════════
# 4. COUNTER-ARGUMENT ENGINE
# ══════════════════════════════════════════════════════════════

_COUNTER_SYSTEM = """You are a steelman generator. Given a position, construct the strongest
possible opposing argument — not a strawman, the actual best case against it. Return JSON:
{
  "original_position": "...",
  "steelman": "the strongest possible opposing argument in 2-4 sentences",
  "key_challenges": ["specific empirical or logical challenges to the original"],
  "competing_explanations": [
    {"explanation": "...", "probability": 0.0}
  ],
  "original_position_probability": 0.0,
  "verdict": "original_likely|roughly_equal|counter_likely|indeterminate"
}
competing_explanations probabilities must sum to <= 1.0 (remaining = original position)"""


def generate_counter(position: str, context: Optional[str] = None) -> Dict:
    try:
        user = f"Position: {position}" + (f"\nContext: {context}" if context else "")
        return _ai_json(_COUNTER_SYSTEM, user)
    except Exception:
        return {
            "error": "AI unavailable",
            "original_position": position,
            "steelman": "(unavailable)",
            "key_challenges": [],
            "competing_explanations": [],
            "verdict": "indeterminate",
        }


# ══════════════════════════════════════════════════════════════
# 5. DECISION AUTOPSY
# ══════════════════════════════════════════════════════════════

_AUTOPSY_PATH = lambda: _data_dir() / "decision_autopsies.jsonl"

OUTCOME_MATRIX = {
    ("good", "good"): {
        "label": "CORRECT",
        "learn": "Process worked. Document it.",
    },
    ("good", "bad"): {
        "label": "BAD_LUCK",
        "learn": "Right process, wrong outcome. Don't change the process.",
    },
    ("bad", "good"): {
        "label": "LUCKY",
        "learn": "Dangerous. You got away with bad reasoning. Fix the process.",
    },
    ("bad", "bad"): {
        "label": "DESERVED",
        "learn": "Bad process, bad outcome. Clear case for change.",
    },
}


def classify_decision(decision_quality: str, outcome_quality: str) -> Dict:
    key = (decision_quality.lower(), outcome_quality.lower())
    matrix = OUTCOME_MATRIX.get(
        key,
        {
            "label": "UNKNOWN",
            "learn": "Classify decision and outcome as good or bad.",
        },
    )
    return matrix


# ══════════════════════════════════════════════════════════════
# 6. COUNTERFACTUAL DIARY
# ══════════════════════════════════════════════════════════════

_CF_PATH = lambda: _data_dir() / "counterfactuals.jsonl"


# ══════════════════════════════════════════════════════════════
# 7. ERROR TAXONOMY LOGGER
# ══════════════════════════════════════════════════════════════

_ERR_PATH = lambda: _data_dir() / "error_taxonomy.jsonl"

ERROR_TYPES = {
    "BASE_RATE_NEGLECT": "Ignored how common/rare something is",
    "OVERCONFIDENCE": "Confidence exceeded accuracy",
    "SCOPE_INSENSITIVITY": "Scale didn't affect intuition appropriately",
    "ANCHORING": "Over-relied on first information",
    "AVAILABILITY": "Judged probability by ease of recall",
    "PLANNING_FALLACY": "Underestimated time/cost/risk",
    "CONFIRMATION": "Sought evidence that confirms existing belief",
    "HINDSIGHT": "Past seems more predictable in retrospect",
    "SUNK_COST": "Continued due to past investment not future value",
    "NARRATIVE_FALLACY": "Created coherent story from random events",
    "CONJUNCTION_FALLACY": "Specific scenario rated more likely than general",
    "ILLUSION_OF_CONTROL": "Overestimated influence over outcomes",
    "STATUS_QUO": "Preferred current state without justification",
    "UNKNOWN": "Unclassified error",
}


def error_pattern_analysis(errors: List[Dict]) -> Dict:
    counts: Dict[str, int] = defaultdict(int)
    for e in errors:
        counts[e.get("error_type", "UNKNOWN")] += 1
    total = len(errors)
    if not total:
        return {"patterns": [], "dominant_error": None, "total": 0}
    sorted_errors = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "total": total,
        "patterns": [
            {
                "type": k,
                "count": v,
                "rate": round(v / total, 3),
                "description": ERROR_TYPES.get(k, "?"),
            }
            for k, v in sorted_errors
        ],
        "dominant_error": sorted_errors[0][0] if sorted_errors else None,
    }


# ══════════════════════════════════════════════════════════════
# 8. ABSTRACTION LADDER
# ══════════════════════════════════════════════════════════════

_ABS_SYSTEM = """You are an abstraction engine. Given a concept, generate all 5 levels
of the abstraction ladder. Return JSON:
{
  "concept": "...",
  "levels": {
    "1_concrete": "specific real-world example with details",
    "2_mechanism": "how it works — the causal process",
    "3_formal": "the abstract principle or formal model",
    "4_analogy": "cross-domain analogy to a completely different field",
    "5_meta": "what category of pattern this represents across all domains"
  },
  "insight": "what becomes visible only at the highest level of abstraction"
}"""


def climb_abstraction_ladder(concept: str) -> Dict:
    try:
        return _ai_json(_ABS_SYSTEM, f"Concept: {concept}")
    except Exception:
        return {
            "error": "AI unavailable",
            "concept": concept,
            "levels": {f"{i}_level": "(unavailable)" for i in range(1, 6)},
        }


# ══════════════════════════════════════════════════════════════
# 9. CONCEPT DEPENDENCY GRAPH
# ══════════════════════════════════════════════════════════════

_CDG_SYSTEM = """You are a knowledge prerequisite mapper. Given a concept, identify
what you need to understand first. Return JSON:
{
  "concept": "...",
  "prerequisites": [
    {"concept": "...", "depth": "foundational|important|helpful", "reason": "why needed"}
  ],
  "estimated_learning_path": ["ordered list of concepts to learn, start to finish"],
  "common_misconception": "the most common wrong mental model people have about this"
}"""


def map_prerequisites(concept: str) -> Dict:
    try:
        return _ai_json(_CDG_SYSTEM, f"Concept to understand: {concept}")
    except Exception:
        return {
            "error": "AI unavailable",
            "concept": concept,
            "prerequisites": [],
            "estimated_learning_path": [concept],
        }


# ══════════════════════════════════════════════════════════════
# 10. CAUSALITY SANDBOX
# ══════════════════════════════════════════════════════════════

_DAG_PATH = lambda: _data_dir() / "causal_dags.json"
_CAUSAL_SYSTEM = """You are a causal inference engine. Given a scenario, build a causal DAG. Return JSON:
{
  "variables": [{"name": "...", "type": "cause|effect|confounder|mediator|collider"}],
  "edges": [{"from": "...", "to": "...", "strength": "strong|moderate|weak", "direction": "positive|negative"}],
  "confounders": ["variables that affect both cause and effect"],
  "interventions": [
    {"action": "if you intervene on X", "predicted_effect": "Y changes because..."}
  ],
  "key_insight": "the non-obvious causal relationship in this scenario"
}"""


def build_causal_dag(scenario: str) -> Dict:
    try:
        return _ai_json(_CAUSAL_SYSTEM, f"Scenario: {scenario}", max_tokens=1200)
    except Exception:
        return {
            "error": "AI unavailable",
            "scenario": scenario,
            "variables": [],
            "edges": [],
            "confounders": [],
        }


# ══════════════════════════════════════════════════════════════
# 11. SOURCE RELIABILITY MAP
# ══════════════════════════════════════════════════════════════

_SRC_PATH = lambda: _data_dir() / "source_reliability.json"


def _load_sources() -> Dict:
    return _load_json(_SRC_PATH(), {})


def source_record_claim(source: str, claim: str, claimed_probability: float) -> str:
    sources = _load_sources()
    cid = _uid()
    if source not in sources:
        sources[source] = {
            "name": source,
            "claims": [],
            "resolved_count": 0,
            "avg_brier": None,
            "reliability_score": None,
            "created_at": _utc(),
        }
    sources[source]["claims"].append(
        {
            "id": cid,
            "claim": claim,
            "claimed_probability": claimed_probability,
            "outcome": None,
            "brier_score": None,
            "created_at": _utc(),
        }
    )
    _save_json(_SRC_PATH(), sources)
    return cid


def source_resolve_claim(source: str, claim_id: str, outcome: bool) -> Dict:
    sources = _load_sources()
    if source not in sources:
        raise ValueError(f"Source {source} not found")
    src = sources[source]
    for c in src["claims"]:
        if c["id"] == claim_id:
            c["outcome"] = outcome
            c["brier_score"] = brier_score(c["claimed_probability"], outcome)
            c["resolved_at"] = _utc()
            break
    resolved = [c for c in src["claims"] if c.get("brier_score") is not None]
    src["resolved_count"] = len(resolved)
    if resolved:
        avg = sum(c["brier_score"] for c in resolved) / len(resolved)
        src["avg_brier"] = round(avg, 4)
        src["reliability_score"] = round(1.0 - (avg / 0.25), 3)
    _save_json(_SRC_PATH(), sources)
    return src


# ══════════════════════════════════════════════════════════════
# 12. ATTENTION AUDIT
# ══════════════════════════════════════════════════════════════

_ATT_PATH = lambda: _data_dir() / "attention_audit.jsonl"


# ══════════════════════════════════════════════════════════════
# 13. MEMORY DISTORTION LOGGER
# ══════════════════════════════════════════════════════════════

_MEM_PATH = lambda: _data_dir() / "memory_distortions.jsonl"


def memory_distortion_score(immediate: str, delayed: str) -> Dict:
    def tokens(s):
        return set(re.findall(r"\b\w+\b", s.lower()))

    t1, t2 = tokens(immediate), tokens(delayed)
    if not t1:
        return {"overlap": 0.0, "added": list(t2), "lost": [], "distortion": 1.0}
    overlap = len(t1 & t2) / len(t1 | t2) if (t1 | t2) else 1.0
    return {
        "overlap_score": round(overlap, 3),
        "distortion_score": round(1.0 - overlap, 3),
        "tokens_lost": list(t1 - t2)[:10],
        "tokens_added": list(t2 - t1)[:10],
        "severity": "low" if overlap > 0.8 else "medium" if overlap > 0.5 else "high",
    }


# ══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════


class PredictionCreate(BaseModel):
    claim: str = Field(..., min_length=5)
    probability: float = Field(..., ge=0.0, le=1.0)
    resolve_by: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PredictionResolve(BaseModel):
    outcome: bool


class DependencyCreate(BaseModel):
    from_belief_id: str
    to_belief_id: str
    strength: float = Field(1.0, ge=0.0, le=1.0)


class ArgumentRequest(BaseModel):
    argument: str = Field(..., min_length=10)


class CounterRequest(BaseModel):
    position: str = Field(..., min_length=5)
    context: Optional[str] = None


class DecisionAutopsyCreate(BaseModel):
    description: str = Field(..., min_length=5)
    decision_quality: str = Field(..., pattern="^(good|bad)$")
    outcome_quality: str = Field(..., pattern="^(good|bad)$")
    reasoning: Optional[str] = None
    what_to_change: Optional[str] = None


class CounterfactualCreate(BaseModel):
    event: str = Field(..., min_length=5)
    actual_outcome: str = Field(..., min_length=5)
    context: Optional[str] = None


class ErrorCreate(BaseModel):
    description: str = Field(..., min_length=5)
    error_type: str = "UNKNOWN"
    context: Optional[str] = None
    mission_id: Optional[str] = None


class AbstractionRequest(BaseModel):
    concept: str = Field(..., min_length=2)


class PrerequisiteRequest(BaseModel):
    concept: str = Field(..., min_length=2)


class CausalRequest(BaseModel):
    scenario: str = Field(..., min_length=10)


class SourceClaimCreate(BaseModel):
    source: str = Field(..., min_length=2)
    claim: str = Field(..., min_length=5)
    claimed_probability: float = Field(..., ge=0.0, le=1.0)


class SourceClaimResolve(BaseModel):
    claim_id: str
    outcome: bool


class AttentionSessionCreate(BaseModel):
    task: str = Field(..., min_length=3)
    duration_minutes: float = Field(..., gt=0)
    interruptions: int = Field(0, ge=0)
    task_switches: int = Field(0, ge=0)
    rereads: int = Field(0, ge=0)
    quality_rating: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None


class MemoryCreate(BaseModel):
    topic: str = Field(..., min_length=3)
    immediate_recall: str = Field(..., min_length=5)


class MemoryDelayed(BaseModel):
    delayed_recall: str = Field(..., min_length=5)


# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════

router = APIRouter()


@router.post("/v1/cognition/predictions", status_code=201)
async def create_prediction(payload: PredictionCreate):
    pid = _uid()
    record = {
        "id": pid,
        "claim": payload.claim,
        "probability": payload.probability,
        "resolve_by": payload.resolve_by,
        "category": payload.category,
        "tags": payload.tags,
        "resolved": False,
        "outcome": None,
        "brier_score": None,
        "created_at": _utc(),
    }
    _append_jsonl(_PRED_PATH(), record)
    try:
        from nexusmon_operator_rank import award_xp as _rank_xp
        _rank_xp("log_prediction", detail=pid)
    except Exception:
        pass
    return {"ok": True, "prediction_id": pid, "prediction": record}


@router.get("/v1/cognition/predictions")
async def list_predictions(resolved: Optional[bool] = None, category: Optional[str] = None):
    preds = _load_jsonl(_PRED_PATH())
    if resolved is not None:
        preds = [p for p in preds if p.get("resolved") == resolved]
    if category:
        preds = [p for p in preds if p.get("category") == category]
    preds.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return {
        "ok": True,
        "predictions": preds,
        "count": len(preds),
        "avg_brier": avg_brier(preds),
        "calibration": calibration_buckets(preds),
    }


@router.patch("/v1/cognition/predictions/{pid}/resolve")
async def resolve_prediction(pid: str, payload: PredictionResolve):
    preds = _load_jsonl(_PRED_PATH())
    for p in preds:
        if p["id"] == pid:
            p["outcome"] = payload.outcome
            p["resolved"] = True
            p["brier_score"] = brier_score(p["probability"], payload.outcome)
            p["resolved_at"] = _utc()
            _rewrite_jsonl(_PRED_PATH(), preds)
            return {
                "ok": True,
                "prediction_id": pid,
                "brier_score": p["brier_score"],
                "verdict": "correct"
                if (p["probability"] > 0.5) == payload.outcome
                else "incorrect",
            }
    raise HTTPException(404, f"Prediction {pid} not found")


@router.get("/v1/cognition/predictions/calibration")
async def get_calibration():
    preds = _load_jsonl(_PRED_PATH())
    return {
        "ok": True,
        "avg_brier": avg_brier(preds),
        "buckets": calibration_buckets(preds),
        "total_resolved": len([p for p in preds if p.get("resolved")]),
        "total_unresolved": len([p for p in preds if not p.get("resolved")]),
        "interpretation": {
            "perfect_brier": 0.0,
            "random_brier": 0.25,
            "your_brier": avg_brier(preds),
        },
    }


@router.post("/v1/cognition/belief-graph/dependency")
async def add_dependency(payload: DependencyCreate):
    bdg_add_dependency(payload.from_belief_id, payload.to_belief_id, payload.strength)
    return {
        "ok": True,
        "edge": {
            "from": payload.from_belief_id,
            "to": payload.to_belief_id,
            "strength": payload.strength,
        },
    }


@router.get("/v1/cognition/belief-graph")
async def get_belief_graph():
    g = _load_graph()
    return {"ok": True, "nodes": len(g["nodes"]), "edges": len(g["edges"]), "graph": g}


@router.post("/v1/cognition/belief-graph/cascade/{belief_id}")
async def cascade_from_belief(
    belief_id: str, old_confidence: float = 0.8, new_confidence: float = 0.5
):
    g = _load_graph()
    node = g["nodes"].get(belief_id)
    if not node:
        try:
            beliefs = _load_jsonl(_data_dir() / "beliefs.jsonl")
            b = next((b for b in beliefs if b["id"] == belief_id), None)
            if b:
                bdg_add_node(belief_id, b["claim"], b.get("confidence", 0.5))
        except Exception:
            pass
    affected = bdg_cascade(belief_id, old_confidence, new_confidence)
    return {
        "ok": True,
        "belief_id": belief_id,
        "delta": round(new_confidence - old_confidence, 3),
        "affected_beliefs": affected,
        "affected_count": len(affected),
    }


@router.post("/v1/cognition/argument/compile")
async def compile_arg(payload: ArgumentRequest):
    result = compile_argument(payload.argument)
    record = {
        "id": _uid(),
        "argument": payload.argument,
        "analysis": result,
        "created_at": _utc(),
    }
    _append_jsonl(_data_dir() / "arguments.jsonl", record)
    return {"ok": True, "record_id": record["id"], "analysis": result}


@router.post("/v1/cognition/argument/counter")
async def counter_argument(payload: CounterRequest):
    result = generate_counter(payload.position, payload.context)
    record = {
        "id": _uid(),
        "position": payload.position,
        "counter": result,
        "created_at": _utc(),
    }
    _append_jsonl(_data_dir() / "counter_arguments.jsonl", record)
    return {"ok": True, "record_id": record["id"], "counter": result}


@router.post("/v1/cognition/autopsy", status_code=201)
async def create_autopsy(payload: DecisionAutopsyCreate):
    classification = classify_decision(payload.decision_quality, payload.outcome_quality)
    record = {
        "id": _uid(),
        "description": payload.description,
        "decision_quality": payload.decision_quality,
        "outcome_quality": payload.outcome_quality,
        "classification": classification["label"],
        "lesson": classification["learn"],
        "reasoning": payload.reasoning,
        "what_to_change": payload.what_to_change,
        "created_at": _utc(),
    }
    _append_jsonl(_AUTOPSY_PATH(), record)
    try:
        from nexusmon_operator_rank import award_xp as _rank_xp
        _rank_xp("decision_autopsy", detail=record["id"])
    except Exception:
        pass
    return {
        "ok": True,
        "autopsy_id": record["id"],
        "classification": classification["label"],
        "lesson": classification["learn"],
    }


@router.get("/v1/cognition/autopsy")
async def list_autopsies():
    autopsies = _load_jsonl(_AUTOPSY_PATH())
    counts = defaultdict(int)
    for a in autopsies:
        counts[a.get("classification", "UNKNOWN")] += 1
    return {
        "ok": True,
        "autopsies": autopsies[-20:],
        "total": len(autopsies),
        "classification_summary": dict(counts),
    }


@router.post("/v1/cognition/counterfactual", status_code=201)
async def create_counterfactual(payload: CounterfactualCreate):
    system = """You are a counterfactual analyst. Return JSON:
{"actual_outcome":"...","alternatives":[{"outcome":"...","probability":0.0,"key_difference":"..."}],
"hindsight_risk":"low|medium|high","hindsight_risk_reasoning":"one sentence"}"""
    try:
        analysis = _ai_json(
            system,
            f"Event: {payload.event}\nActual outcome: {payload.actual_outcome}"
            + (f"\nContext: {payload.context}" if payload.context else ""),
        )
    except Exception:
        analysis = {
            "actual_outcome": payload.actual_outcome,
            "alternatives": [],
            "hindsight_risk": "unknown",
            "hindsight_risk_reasoning": "AI unavailable",
        }
    record = {
        "id": _uid(),
        "event": payload.event,
        "actual_outcome": payload.actual_outcome,
        "analysis": analysis,
        "created_at": _utc(),
    }
    _append_jsonl(_CF_PATH(), record)
    return {"ok": True, "counterfactual_id": record["id"], "analysis": analysis}


@router.get("/v1/cognition/counterfactual")
async def list_counterfactuals():
    cfs = _load_jsonl(_CF_PATH())
    hindsight_counts = defaultdict(int)
    for c in cfs:
        hindsight_counts[c.get("analysis", {}).get("hindsight_risk", "unknown")] += 1
    return {
        "ok": True,
        "counterfactuals": cfs[-20:],
        "total": len(cfs),
        "hindsight_risk_summary": dict(hindsight_counts),
    }


@router.post("/v1/cognition/errors", status_code=201)
async def log_error(payload: ErrorCreate):
    if payload.error_type not in ERROR_TYPES and payload.error_type != "UNKNOWN":
        try:
            types_list = "\n".join(f"{k}: {v}" for k, v in ERROR_TYPES.items())
            result = _ai_json(
                f"Classify this reasoning error into one of these types:\n{types_list}\nReturn JSON: {{\"error_type\": \"TYPE_NAME\"}}",
                f"Error description: {payload.description}",
            )
            payload.error_type = result.get("error_type", "UNKNOWN")
        except Exception:
            pass

    record = {
        "id": _uid(),
        "description": payload.description,
        "error_type": payload.error_type,
        "error_description": ERROR_TYPES.get(payload.error_type, "Unknown type"),
        "context": payload.context,
        "mission_id": payload.mission_id,
        "created_at": _utc(),
    }
    _append_jsonl(_ERR_PATH(), record)
    try:
        from nexusmon_operator_rank import award_xp as _rank_xp
        _rank_xp("log_cognition_error", detail=record["id"])
    except Exception:
        pass
    return {"ok": True, "error_id": record["id"], "classified_as": record["error_type"]}


@router.get("/v1/cognition/errors")
async def list_errors(error_type: Optional[str] = None):
    errors = _load_jsonl(_ERR_PATH())
    if error_type:
        errors = [e for e in errors if e.get("error_type") == error_type]
    patterns = error_pattern_analysis(errors)
    return {"ok": True, "errors": errors[-30:], "total": len(errors), "patterns": patterns}


@router.get("/v1/cognition/errors/taxonomy")
async def get_taxonomy():
    return {
        "ok": True,
        "taxonomy": {k: {"label": k, "description": v} for k, v in ERROR_TYPES.items()},
    }


@router.post("/v1/cognition/abstraction")
async def abstract_concept(payload: AbstractionRequest):
    result = climb_abstraction_ladder(payload.concept)
    record = {
        "id": _uid(),
        "concept": payload.concept,
        "ladder": result,
        "created_at": _utc(),
    }
    _append_jsonl(_data_dir() / "abstractions.jsonl", record)
    return {"ok": True, "record_id": record["id"], "ladder": result}


@router.post("/v1/cognition/prerequisites")
async def get_prerequisites(payload: PrerequisiteRequest):
    result = map_prerequisites(payload.concept)
    record = {"id": _uid(), "concept": payload.concept, "map": result, "created_at": _utc()}
    _append_jsonl(_data_dir() / "concept_maps.jsonl", record)
    return {"ok": True, "record_id": record["id"], "prerequisites": result}


@router.post("/v1/cognition/causality")
async def build_dag(payload: CausalRequest):
    result = build_causal_dag(payload.scenario)
    record = {"id": _uid(), "scenario": payload.scenario, "dag": result, "created_at": _utc()}
    dags = _load_json(_DAG_PATH(), [])
    dags.append(record)
    _save_json(_DAG_PATH(), dags[-50:])
    return {"ok": True, "dag_id": record["id"], "dag": result}


@router.get("/v1/cognition/causality")
async def list_dags():
    dags = _load_json(_DAG_PATH(), [])
    return {"ok": True, "dags": dags[-10:], "total": len(dags)}


@router.post("/v1/cognition/sources/claim", status_code=201)
async def record_source_claim(payload: SourceClaimCreate):
    cid = source_record_claim(payload.source, payload.claim, payload.claimed_probability)
    return {"ok": True, "claim_id": cid, "source": payload.source}


@router.patch("/v1/cognition/sources/{source}/resolve")
async def resolve_source_claim(source: str, payload: SourceClaimResolve):
    try:
        src = source_resolve_claim(source, payload.claim_id, payload.outcome)
        return {
            "ok": True,
            "source": source,
            "reliability_score": src.get("reliability_score"),
            "avg_brier": src.get("avg_brier"),
            "resolved_count": src.get("resolved_count"),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/v1/cognition/sources")
async def list_sources():
    sources = _load_sources()
    ranked = sorted(
        sources.values(), key=lambda s: s.get("reliability_score") or -999, reverse=True
    )
    return {"ok": True, "sources": ranked, "count": len(sources)}


@router.post("/v1/cognition/attention", status_code=201)
async def log_attention(payload: AttentionSessionCreate):
    focus_score = round(
        payload.quality_rating
        * (1 - min(1.0, payload.interruptions / 10))
        * (1 - min(1.0, payload.task_switches / 5)),
        3,
    )
    record = {
        "id": _uid(),
        "task": payload.task,
        "duration_minutes": payload.duration_minutes,
        "interruptions": payload.interruptions,
        "task_switches": payload.task_switches,
        "rereads": payload.rereads,
        "quality_rating": payload.quality_rating,
        "focus_score": focus_score,
        "notes": payload.notes,
        "created_at": _utc(),
    }
    _append_jsonl(_ATT_PATH(), record)
    return {"ok": True, "session_id": record["id"], "focus_score": focus_score}


@router.get("/v1/cognition/attention")
async def get_attention_stats():
    sessions = _load_jsonl(_ATT_PATH())
    if not sessions:
        return {"ok": True, "sessions": [], "avg_focus_score": None, "total": 0}
    avg_focus = round(sum(s.get("focus_score", 0) for s in sessions) / len(sessions), 3)
    avg_interruptions = round(
        sum(s.get("interruptions", 0) for s in sessions) / len(sessions), 2
    )
    return {
        "ok": True,
        "sessions": sessions[-20:],
        "total": len(sessions),
        "avg_focus_score": avg_focus,
        "avg_interruptions_per_session": avg_interruptions,
        "worst_sessions": sorted(sessions, key=lambda s: s.get("focus_score", 1))[:3],
    }


@router.post("/v1/cognition/memory", status_code=201)
async def create_memory(payload: MemoryCreate):
    mid = _uid()
    record = {
        "id": mid,
        "topic": payload.topic,
        "immediate_recall": payload.immediate_recall,
        "delayed_recall": None,
        "distortion": None,
        "created_at": _utc(),
        "recalled_at": None,
    }
    _append_jsonl(_MEM_PATH(), record)
    return {
        "ok": True,
        "memory_id": mid,
        "instruction": "Come back later and call PATCH /v1/cognition/memory/{id} with your delayed recall.",
    }


@router.patch("/v1/cognition/memory/{mid}")
async def recall_memory(mid: str, payload: MemoryDelayed):
    records = _load_jsonl(_MEM_PATH())
    for r in records:
        if r["id"] == mid:
            distortion = memory_distortion_score(r["immediate_recall"], payload.delayed_recall)
            r["delayed_recall"] = payload.delayed_recall
            r["distortion"] = distortion
            r["recalled_at"] = _utc()
            _rewrite_jsonl(_MEM_PATH(), records)
            return {
                "ok": True,
                "memory_id": mid,
                "distortion": distortion,
                "immediate_recall": r["immediate_recall"],
                "delayed_recall": payload.delayed_recall,
            }
    raise HTTPException(404, f"Memory {mid} not found")


@router.get("/v1/cognition/memory")
async def list_memories():
    records = _load_jsonl(_MEM_PATH())
    resolved = [r for r in records if r.get("distortion")]
    avg_distortion = None
    if resolved:
        avg_distortion = round(
            sum(r["distortion"]["distortion_score"] for r in resolved) / len(resolved), 3
        )
    return {
        "ok": True,
        "memories": records[-20:],
        "total": len(records),
        "resolved": len(resolved),
        "pending_recall": len(records) - len(resolved),
        "avg_distortion_score": avg_distortion,
    }


@router.get("/v1/cognition/status")
async def cognition_status():
    preds = _load_jsonl(_PRED_PATH())
    errors = _load_jsonl(_ERR_PATH())
    autopsies = _load_jsonl(_AUTOPSY_PATH())
    memories = _load_jsonl(_MEM_PATH())
    sessions = _load_jsonl(_ATT_PATH())
    sources = _load_sources()
    g = _load_graph()

    resolved_mems = [m for m in memories if m.get("distortion")]
    avg_mem_distortion = None
    if resolved_mems:
        avg_mem_distortion = round(
            sum(m["distortion"]["distortion_score"] for m in resolved_mems) / len(resolved_mems),
            3,
        )

    errors_pattern = error_pattern_analysis(errors)
    return {
        "ok": True,
        "predictions": {
            "total": len(preds),
            "resolved": len([p for p in preds if p.get("resolved")]),
            "avg_brier": avg_brier(preds),
        },
        "beliefs": {
            "graph_nodes": len(g["nodes"]),
            "graph_edges": len(g["edges"]),
        },
        "errors": {
            "total": len(errors),
            "patterns": errors_pattern.get("patterns", [])[:3],
            "dominant": errors_pattern.get("dominant_error"),
        },
        "decisions": {
            "total_autopsies": len(autopsies),
            "classifications": {
                k: sum(1 for a in autopsies if a.get("classification") == k)
                for k in ["CORRECT", "BAD_LUCK", "LUCKY", "DESERVED"]
            },
        },
        "memory": {
            "total": len(memories),
            "avg_distortion": avg_mem_distortion,
        },
        "attention": {
            "sessions": len(sessions),
            "avg_focus": round(
                sum(s.get("focus_score", 0) for s in sessions) / len(sessions), 3
            )
            if sessions
            else None,
        },
        "sources": {
            "tracked": len(sources),
            "top_source": max(
                sources.values(), key=lambda s: s.get("reliability_score") or -999, default=None
            )
            if sources
            else None,
        },
    }


def fuse_cognition(app) -> None:
    app.include_router(router)
    print("NEXUSMON cognition layer online (13 systems).")
