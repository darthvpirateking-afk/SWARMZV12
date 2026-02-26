# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
"""
ClaimLab API Routes — Epistemic reasoning scaffolding inside NEXUSMON.

Endpoints:
  POST /v1/claimlab/analyze        — Decompose a claim into structured reasoning
  POST /v1/claimlab/beliefs        — Log a belief with confidence level
  GET  /v1/claimlab/beliefs        — List tracked beliefs
  PATCH /v1/claimlab/beliefs/{id}  — Revise a belief (Bayesian update)
  GET  /v1/claimlab/beliefs/{id}   — Get single belief with full revision history
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/claimlab", tags=["ClaimLab"])

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

BELIEFS_FILE = Path(os.environ.get("DATABASE_URL", "data/nexusmon.db")).parent / "beliefs.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_beliefs() -> List[Dict]:
    BELIEFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not BELIEFS_FILE.exists():
        return []
    beliefs = []
    with open(BELIEFS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    beliefs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return beliefs


def _save_belief(belief: Dict) -> None:
    BELIEFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BELIEFS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(belief) + "\n")


def _rewrite_beliefs(beliefs: List[Dict]) -> None:
    BELIEFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BELIEFS_FILE, "w", encoding="utf-8") as f:
        for b in beliefs:
            f.write(json.dumps(b) + "\n")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    claim: str = Field(..., min_length=5, description="The claim to analyze")
    context: Optional[str] = Field(None, description="Optional surrounding context (article, conversation)")


class AnalyzeResponse(BaseModel):
    ok: bool
    claim: str
    analysis: Dict[str, Any]
    source: str


class BeliefCreateRequest(BaseModel):
    claim: str = Field(..., min_length=5)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Initial confidence 0.0–1.0")
    rationale: Optional[str] = Field(None, description="Why you hold this belief")
    tags: List[str] = Field(default_factory=list)


class BeliefReviseRequest(BaseModel):
    confidence: float = Field(..., ge=0.0, le=1.0, description="Updated confidence after new evidence")
    evidence: str = Field(..., min_length=3, description="What evidence triggered this revision")


# ---------------------------------------------------------------------------
# Claim analysis — AI-powered decomposition
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are ClaimLab, an epistemic analysis engine. Your only job is to decompose claims into structured reasoning scaffolding. You do not render verdicts or declare claims true or false. You reveal structure.

When given a claim, return ONLY a JSON object with exactly these keys:

{
  "exact_claim": "The precise, stripped claim with no paraphrase added",
  "claim_type": "descriptive | normative | mixed",
  "claim_type_reasoning": "One sentence explaining the classification",
  "component_claims": ["list", "of", "atomic", "sub-claims", "if compound"],
  "falsifiability": {
    "falsifiable": true | false,
    "conditions_that_would_falsify": ["list"],
    "conditions_that_would_support": ["list"]
  },
  "measurable_quantities": ["any", "implied", "measurable", "variables"],
  "cognitive_biases_at_play": [
    {"bias": "name", "explanation": "why it's relevant here"}
  ],
  "uncertainty_level": "low | medium | high | indeterminate",
  "uncertainty_reasoning": "One sentence"
}

Return only valid JSON. No preamble, no markdown fences."""


def _analyze_with_ai(claim: str, context: Optional[str]) -> Dict[str, Any]:
    """Call Anthropic API to decompose the claim."""
    import anthropic  # type: ignore

    client = anthropic.Anthropic()
    user_content = f"Claim: {claim}"
    if context:
        user_content += f"\n\nContext: {context}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if model adds them despite instructions
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
    return json.loads(raw)


def _analyze_fallback(claim: str) -> Dict[str, Any]:
    """Minimal structural fallback when AI is unavailable."""
    words = claim.lower().split()
    normative_markers = {"should", "must", "ought", "better", "worse", "good", "bad", "right", "wrong"}
    is_normative = bool(normative_markers & set(words))
    return {
        "exact_claim": claim,
        "claim_type": "normative" if is_normative else "descriptive",
        "claim_type_reasoning": "Heuristic keyword detection (AI unavailable).",
        "component_claims": [claim],
        "falsifiability": {
            "falsifiable": not is_normative,
            "conditions_that_would_falsify": ["(AI unavailable — supply manually)"],
            "conditions_that_would_support": ["(AI unavailable — supply manually)"],
        },
        "measurable_quantities": [],
        "cognitive_biases_at_play": [],
        "uncertainty_level": "indeterminate",
        "uncertainty_reasoning": "AI analysis unavailable; structural heuristics only.",
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_claim(payload: AnalyzeRequest):
    """
    Decompose any claim into structured epistemic scaffolding.

    Returns claim type, falsifiability conditions, measurable quantities,
    and cognitive biases — without rendering a verdict.
    """
    try:
        analysis = _analyze_with_ai(payload.claim, payload.context)
        source = "ai"
    except Exception as e:
        logger.warning("ClaimLab AI analysis failed, using fallback: %s", e)
        analysis = _analyze_fallback(payload.claim)
        source = "heuristic_fallback"

    try:
        from nexusmon_organism import ctx_record_message
        ctx_record_message(payload.claim, "operator")
    except Exception:
        pass

    return AnalyzeResponse(ok=True, claim=payload.claim, analysis=analysis, source=source)


@router.post("/beliefs", status_code=201)
async def create_belief(payload: BeliefCreateRequest):
    """
    Log a belief with an explicit confidence level.

    Confidence is 0.0–1.0. Beliefs are revisable — each PATCH records a
    revision event, so you accumulate a calibration history over time.
    """
    belief_id = str(uuid4())
    now = _utc_now()
    belief = {
        "id": belief_id,
        "claim": payload.claim,
        "confidence": payload.confidence,
        "rationale": payload.rationale,
        "tags": payload.tags,
        "created_at": now,
        "revised_at": now,
        "revision_count": 0,
        "revision_history": [],
        "status": "active",
    }
    _save_belief(belief)
    return {"ok": True, "belief_id": belief_id, "belief": belief}


@router.get("/beliefs")
async def list_beliefs(tag: Optional[str] = None, min_confidence: float = 0.0):
    """
    List all tracked beliefs.

    Filter by tag or minimum confidence level. Ordered newest-first.
    """
    beliefs = _load_beliefs()
    active = [b for b in beliefs if b.get("status") == "active"]
    if tag:
        active = [b for b in active if tag in b.get("tags", [])]
    if min_confidence > 0:
        active = [b for b in active if b.get("confidence", 0) >= min_confidence]
    active.sort(key=lambda b: b.get("revised_at", ""), reverse=True)
    return {"ok": True, "beliefs": active, "count": len(active)}


@router.get("/beliefs/{belief_id}")
async def get_belief(belief_id: str):
    """Get a single belief with its full revision history."""
    beliefs = _load_beliefs()
    belief = next((b for b in beliefs if b.get("id") == belief_id), None)
    if not belief:
        raise HTTPException(status_code=404, detail=f"Belief {belief_id} not found")
    return {"ok": True, "belief": belief}


@router.patch("/beliefs/{belief_id}")
async def revise_belief(belief_id: str, payload: BeliefReviseRequest):
    """
    Revise a belief's confidence based on new evidence.

    This is Bayesian updating made explicit — the old confidence, new
    confidence, and triggering evidence are all logged in revision_history.
    You accumulate a record of how well-calibrated you actually are.
    """
    beliefs = _load_beliefs()
    idx = next((i for i, b in enumerate(beliefs) if b.get("id") == belief_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Belief {belief_id} not found")

    belief = beliefs[idx]
    old_confidence = belief.get("confidence", 0.5)
    now = _utc_now()

    revision_event = {
        "revised_at": now,
        "old_confidence": old_confidence,
        "new_confidence": payload.confidence,
        "delta": round(payload.confidence - old_confidence, 4),
        "evidence": payload.evidence,
    }

    belief["confidence"] = payload.confidence
    belief["revised_at"] = now
    belief["revision_count"] = belief.get("revision_count", 0) + 1
    belief.setdefault("revision_history", []).append(revision_event)

    beliefs[idx] = belief
    _rewrite_beliefs(beliefs)

    try:
        from nexusmon_organism import ctx_record_belief_revision
        ctx_record_belief_revision(old_confidence, payload.confidence)
    except Exception:
        pass

    return {
        "ok": True,
        "belief_id": belief_id,
        "revision": revision_event,
        "belief": belief,
    }


@router.get("/health", operation_id="claimlab_health")
async def claimlab_health():
    """ClaimLab subsystem health check."""
    try:
        import anthropic  # noqa
        ai_available = True
    except ImportError:
        ai_available = False

    beliefs = _load_beliefs()
    return {
        "ok": True,
        "subsystem": "claimlab",
        "ai_available": ai_available,
        "belief_count": len([b for b in beliefs if b.get("status") == "active"]),
    }
