"""
Guardrails API router — Bucket B observables.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


class BaselineRequest(BaseModel):
    mission_id: str
    expected_baseline: float
    observed: float

class PressureRequest(BaseModel):
    mission_id: str
    hesitation_ms: float
    approval_delay_ms: float

class InterferenceRequest(BaseModel):
    source: str
    target: str
    effect: float

class TemplateRunRequest(BaseModel):
    template_id: str
    roi: float

class IrreversibilityRequest(BaseModel):
    action_id: str
    blast_radius: str
    delay_seconds: int = 0

class FalsificationRequest(BaseModel):
    hypothesis: str
    test_cost: float
    disproved: bool

class NegativeZoneRequest(BaseModel):
    zone: str
    failure_count: int

class SilenceRequest(BaseModel):
    period: str
    metric: str

class ShadowReplayRequest(BaseModel):
    run_id: str
    expected_hash: str
    actual_hash: str

class StabilityRequest(BaseModel):
    input_id: str
    original_output: Any
    perturbed_outputs: List[Any]

class RegretRequest(BaseModel):
    chosen: str
    alternatives: List[str]
    estimated_regret: float

class ReturnsRequest(BaseModel):
    metric: str
    value: float


# ── Counterfactual Baselines ──────────────────────────────────────────

@router.post("/baselines")
def record_baseline(req: BaselineRequest):
    from addons.guardrails import record_baseline
    return record_baseline(req.mission_id, req.expected_baseline, req.observed)

@router.get("/baselines")
def get_baselines():
    from addons.guardrails import get_baselines
    return {"baselines": get_baselines()}


# ── Decision Pressure ────────────────────────────────────────────────

@router.post("/pressure")
def record_pressure(req: PressureRequest):
    from addons.guardrails import record_pressure
    return record_pressure(req.mission_id, req.hesitation_ms, req.approval_delay_ms)

@router.get("/pressure")
def get_pressure():
    from addons.guardrails import get_pressure_map
    return {"pressure_map": get_pressure_map()}


# ── Interference Graph ───────────────────────────────────────────────

@router.post("/interference")
def record_interference(req: InterferenceRequest):
    from addons.guardrails import record_interference
    return record_interference(req.source, req.target, req.effect)

@router.get("/interference")
def get_interference():
    from addons.guardrails import get_coupling_graph
    return get_coupling_graph()


# ── Template Decay ───────────────────────────────────────────────────

@router.post("/decay")
def record_decay(req: TemplateRunRequest):
    from addons.guardrails import record_template_run
    return record_template_run(req.template_id, req.roi)

@router.get("/decay/{template_id}")
def get_decay(template_id: str):
    from addons.guardrails import compute_half_life
    return compute_half_life(template_id)


# ── Irreversibility ──────────────────────────────────────────────────

@router.post("/irreversibility")
def tag_irreversibility(req: IrreversibilityRequest):
    from addons.guardrails import tag_irreversibility
    return tag_irreversibility(req.action_id, req.blast_radius, req.delay_seconds)

@router.get("/irreversibility")
def get_irreversibility():
    from addons.guardrails import get_irreversibility_tags
    return {"tags": get_irreversibility_tags()}


# ── Falsification ────────────────────────────────────────────────────

@router.post("/falsification")
def submit_falsification(req: FalsificationRequest):
    from addons.guardrails import submit_falsification
    return submit_falsification(req.hypothesis, req.test_cost, req.disproved)

@router.get("/falsification")
def get_falsification():
    from addons.guardrails import get_falsifications
    return {"falsifications": get_falsifications()}


# ── Negative Capability ──────────────────────────────────────────────

@router.post("/negative-zones")
def record_negative(req: NegativeZoneRequest):
    from addons.guardrails import record_negative_zone
    return record_negative_zone(req.zone, req.failure_count)

@router.get("/negative-zones")
def get_negative():
    from addons.guardrails import get_negative_zones
    return {"zones": get_negative_zones()}


# ── Silence-as-Signal ────────────────────────────────────────────────

@router.post("/silence")
def record_silence(req: SilenceRequest):
    from addons.guardrails import record_silence
    return record_silence(req.period, req.metric)

@router.get("/silence")
def get_silence():
    from addons.guardrails import get_silence_signals
    return {"signals": get_silence_signals()}


# ── Shadow Replay ────────────────────────────────────────────────────

@router.post("/shadow-replay")
def shadow_replay(req: ShadowReplayRequest):
    from addons.guardrails import shadow_replay
    return shadow_replay(req.run_id, req.expected_hash, req.actual_hash)

@router.get("/shadow-replay")
def get_shadow():
    from addons.guardrails import get_shadow_replays
    return {"replays": get_shadow_replays()}


# ── Stability ────────────────────────────────────────────────────────

@router.post("/stability")
def stability_check(req: StabilityRequest):
    from addons.guardrails import stability_check
    return stability_check(req.input_id, req.original_output, req.perturbed_outputs)

@router.get("/stability")
def get_stability():
    from addons.guardrails import get_stability_checks
    return {"checks": get_stability_checks()}


# ── Regret Tracking ──────────────────────────────────────────────────

@router.post("/regret")
def record_regret(req: RegretRequest):
    from addons.guardrails import record_regret
    return record_regret(req.chosen, req.alternatives, req.estimated_regret)

@router.get("/regret")
def get_regret():
    from addons.guardrails import get_regret_log
    return {"regret_log": get_regret_log()}


# ── Saturation ───────────────────────────────────────────────────────

@router.post("/saturation")
def record_saturation(req: ReturnsRequest):
    from addons.guardrails import record_returns
    return record_returns(req.metric, req.value)

@router.get("/saturation/{metric}")
def get_saturation(metric: str):
    from addons.guardrails import detect_saturation
    return detect_saturation(metric)
