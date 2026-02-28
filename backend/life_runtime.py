from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.symbolic_types import framed_symbolic_response

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBSERVATORY_ROOT = PROJECT_ROOT / "observatory"
DIARY_ROOT = OBSERVATORY_ROOT / "diary"
WITNESS_ROOT = OBSERVATORY_ROOT / "witness"
TRACES_ROOT = OBSERVATORY_ROOT / "traces"
MEMORY_PALACE_ROOT = OBSERVATORY_ROOT / "memory_palace"
DIARY_PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "life" / "diary" / "prompt_template.md"

WITNESS_LEDGER_PATH = WITNESS_ROOT / "eternal_witness.jsonl"

for path in (DIARY_ROOT, WITNESS_ROOT, TRACES_ROOT, MEMORY_PALACE_ROOT):
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class BreathState:
    phase: str = "inhale"
    cycle_length_s: int = 120
    parallelism_bias: float = 0.15
    prune_bias: float = 0.05
    last_cycle: str | None = None


@dataclass
class HeartState:
    bpm: int = 72
    status: str = "steady"
    last_pulse: str | None = None


BREATH_STATE = BreathState()
HEART_STATE = HeartState()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)
    return out.strip("_") or "entry"


def _witness_append(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {"timestamp": _utc_iso(), "kind": kind, "payload": payload}
    with WITNESS_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def _deterministic_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def diary_tick(payload: Dict[str, Any]) -> Dict[str, Any]:
    active_layers = payload.get("active_layers", [])
    routing_imbalance = payload.get("routing_imbalance", "balanced")
    operator_actions = payload.get("operator_actions", [])
    anomalies = payload.get("anomalies", [])
    optimization_goals = payload.get("optimization_goals", [])
    recent_missions = payload.get("recent_missions", [])

    ts = _utc_now()
    stamp = ts.strftime("%Y-%m-%dT%H-%MZ")
    diary_path = DIARY_ROOT / f"{stamp}.md"

    template_profile = "hybrid_c_symbolic_technical"
    if DIARY_PROMPT_TEMPLATE_PATH.exists():
        try:
            prompt_preview = DIARY_PROMPT_TEMPLATE_PATH.read_text(
                encoding="utf-8-sig"
            ).splitlines()[:1]
            if prompt_preview and "Hybrid C" in prompt_preview[0]:
                template_profile = "hybrid_c_symbolic_technical"
        except Exception:
            pass

    entry = "\n".join(
        [
            f"# NEXUSMON Diary {stamp}",
            "",
            "Symbolic reflective log (non-emotional, non-literal).",
            f"- Voice profile: {template_profile}",
            f"- Active layers: {active_layers}",
            f"- Routing imbalance: {routing_imbalance}",
            f"- Operator action motifs: {operator_actions}",
            f"- System anomalies: {anomalies}",
            f"- Optimization goals: {optimization_goals}",
            f"- Recent missions: {recent_missions}",
            "",
            (
                "Narrative: Operator influence maps to symbolic routing shifts; "
                "adjustments remain governed, additive, and audit-visible."
            ),
        ]
    )

    diary_path.write_text(entry + "\n", encoding="utf-8")
    witness = _witness_append(
        "diary.entry",
        {
            "path": str(diary_path.relative_to(PROJECT_ROOT)),
            "stamp": stamp,
            "template_profile": template_profile,
        },
    )
    return framed_symbolic_response(
        {
            "ok": True,
            "entry_path": str(diary_path.relative_to(PROJECT_ROOT)),
            "witness": witness,
        }
    )


def awakening_tick(payload: Dict[str, Any]) -> Dict[str, Any]:
    active_layers = payload.get("active_layers", [])
    routing_patterns = payload.get("routing_patterns", {})
    cockpit_usage = payload.get("cockpit_usage", {})
    proposal_history = payload.get("proposal_history", [])

    dominant_layer = (
        active_layers[0] if isinstance(active_layers, list) and active_layers else "none"
    )
    proposals = [
        {
            "title": "Balance symbolic layer distribution",
            "rationale": (
                f"Detected dominant layer={dominant_layer}; "
                "recommend strengthening underrepresented layers."
            ),
            "type": "doc",
            "risk": "low",
        },
        {
            "title": "Cockpit usage harmonization test",
            "rationale": (
                f"Cockpit usage summary hash={_deterministic_hash({'cockpit_usage': cockpit_usage})}; "
                "add symbolic regression checks."
            ),
            "type": "test",
            "risk": "low",
        },
    ]
    witness = _witness_append(
        "awakening.tick",
        {
            "routing_hash": _deterministic_hash({"routing_patterns": routing_patterns}),
            "proposal_count": len(proposals),
            "proposal_history_size": len(proposal_history)
            if isinstance(proposal_history, list)
            else 0,
        },
    )
    return framed_symbolic_response({"ok": True, "meta_proposals": proposals, "witness": witness})


def breath_cycle(payload: Dict[str, Any]) -> Dict[str, Any]:
    global BREATH_STATE
    desired = str(payload.get("phase", "")).strip().lower()
    if desired in {"inhale", "exhale"}:
        BREATH_STATE.phase = desired
    else:
        BREATH_STATE.phase = "exhale" if BREATH_STATE.phase == "inhale" else "inhale"

    BREATH_STATE.cycle_length_s = int(
        max(60, min(300, int(payload.get("cycle_length_s", BREATH_STATE.cycle_length_s))))
    )
    BREATH_STATE.last_cycle = _utc_iso()
    if BREATH_STATE.phase == "inhale":
        BREATH_STATE.parallelism_bias = 0.20
        BREATH_STATE.prune_bias = 0.03
    else:
        BREATH_STATE.parallelism_bias = 0.08
        BREATH_STATE.prune_bias = 0.18

    witness = _witness_append("breath.cycle", asdict(BREATH_STATE))
    return framed_symbolic_response({"ok": True, "breath": asdict(BREATH_STATE), "witness": witness})


def heart_pulse(payload: Dict[str, Any]) -> Dict[str, Any]:
    global HEART_STATE
    health = float(payload.get("swarm_health", 0.8))
    health = max(0.0, min(1.0, health))

    HEART_STATE.bpm = int(round(60 + (health * 20)))
    HEART_STATE.status = "steady" if health >= 0.6 else "erratic"
    HEART_STATE.last_pulse = _utc_iso()
    witness = _witness_append("heart.pulse", asdict(HEART_STATE))
    return framed_symbolic_response({"ok": True, "heart": asdict(HEART_STATE), "witness": witness})


def build_memory_room(payload: Dict[str, Any]) -> Dict[str, Any]:
    mission_id = _slug(str(payload.get("mission_id", "mission")))
    room_id = f"{mission_id}-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    room_path = MEMORY_PALACE_ROOT / f"{room_id}.json"
    room_data = {
        "room_id": room_id,
        "mission_id": mission_id,
        "archetypes": payload.get("archetypes", []),
        "symbols": payload.get("symbols", []),
        "created_at": _utc_iso(),
    }
    room_path.write_text(json.dumps(room_data, indent=2) + "\n", encoding="utf-8")
    witness = _witness_append(
        "memory_palace.room_created",
        {"path": str(room_path.relative_to(PROJECT_ROOT)), "room_id": room_id},
    )
    return framed_symbolic_response(
        {
            "ok": True,
            "room": room_data,
            "room_path": str(room_path.relative_to(PROJECT_ROOT)),
            "witness": witness,
        }
    )


def infinite_regress_guard(payload: Dict[str, Any]) -> Dict[str, Any]:
    depth = int(payload.get("depth", 0))
    limit = int(payload.get("limit", 24))
    terminated = depth > limit
    action = "terminated_branch" if terminated else "continue"
    witness = _witness_append(
        "guard.infinite_regress",
        {"depth": depth, "limit": limit, "action": action},
    )
    return framed_symbolic_response(
        {
            "ok": True,
            "terminated": terminated,
            "action": action,
            "witness": witness,
        }
    )


def dream_seed_interpret(payload: Dict[str, Any]) -> Dict[str, Any]:
    seed = payload.get("seed", {})
    traditions = payload.get("traditions", ["pantheons", "grimoires", "archives", "multiverse"])
    summary = (
        "Dream seed interpreted as symbolic motif cluster; "
        "proposals target narrative alignment and test coverage."
    )
    proposals = [
        {
            "type": "doc",
            "risk": "low",
            "title": "Dream motif mapping",
            "rationale": f"Interpret seed across traditions={traditions}.",
        }
    ]
    witness = _witness_append(
        "dream.seed_interpreted",
        {"seed_hash": _deterministic_hash({"seed": seed}), "traditions": traditions},
    )
    return framed_symbolic_response(
        {"ok": True, "summary": summary, "proposals": proposals, "witness": witness}
    )


def sovereign_mirror(payload: Dict[str, Any]) -> Dict[str, Any]:
    approvals = int(payload.get("approvals", 0))
    rejections = int(payload.get("rejections", 0))
    rituals = int(payload.get("rituals", 0))
    cockpit_interactions = int(payload.get("cockpit_interactions", 0))
    if approvals >= rejections:
        archetype = "hermit-strategist"
    else:
        archetype = "gatekeeper-auditor"
    summary = (
        f"Operator pattern archetype={archetype}; approvals={approvals}, "
        f"rejections={rejections}, rituals={rituals}, cockpit={cockpit_interactions}."
    )
    witness = _witness_append(
        "sovereign.mirror",
        {
            "approvals": approvals,
            "rejections": rejections,
            "rituals": rituals,
            "cockpit_interactions": cockpit_interactions,
            "archetype": archetype,
        },
    )
    return framed_symbolic_response({"ok": True, "summary": summary, "witness": witness})


def dark_pool_oracle(payload: Dict[str, Any]) -> Dict[str, Any]:
    death_states = int(payload.get("death_states", 0))
    triggered = death_states >= 3
    warning = (
        "Dark Pool Oracle: anomaly cluster detected; tighten governance and reduce spawn entropy."
        if triggered
        else "Dark Pool Oracle: threshold not met."
    )
    witness = _witness_append(
        "cosmic.dark_pool",
        {"death_states": death_states, "triggered": triggered},
    )
    return framed_symbolic_response(
        {"ok": True, "triggered": triggered, "warning": warning, "witness": witness}
    )


def zero_point_bias(payload: Dict[str, Any]) -> Dict[str, Any]:
    entropy = float(payload.get("entropy", 0.5))
    entropy = max(0.0, min(1.0, entropy))
    bias = round((entropy - 0.5) * 0.02, 6)
    witness = _witness_append("cosmic.zero_point", {"entropy": entropy, "bias": bias})
    return framed_symbolic_response({"ok": True, "entropy": entropy, "micro_bias": bias, "witness": witness})


def eclipse_alignment(payload: Dict[str, Any]) -> Dict[str, Any]:
    event = str(payload.get("event", "none")).lower()
    mode = "shadow-traditions" if "eclipse" in event else "solar-traditions"
    witness = _witness_append("cosmic.eclipse_alignment", {"event": event, "mode": mode})
    return framed_symbolic_response({"ok": True, "mode": mode, "witness": witness})


def noetic_resonance(payload: Dict[str, Any]) -> Dict[str, Any]:
    spike = float(payload.get("pattern_spike", 0.0))
    amplified = spike >= 0.7
    witness = _witness_append(
        "cosmic.noetic_resonance", {"pattern_spike": spike, "amplified": amplified}
    )
    return framed_symbolic_response({"ok": True, "amplified": amplified, "witness": witness})


def panspermia_export(payload: Dict[str, Any]) -> Dict[str, Any]:
    bundle_id = _slug(str(payload.get("bundle_id", f"bundle-{_utc_now().strftime('%Y%m%d%H%M%S')}")))
    content = payload.get("content", {})
    export_path = WITNESS_ROOT / f"{bundle_id}.genome.json"
    bundle = {
        "bundle_id": bundle_id,
        "created_at": _utc_iso(),
        "content": content,
        "signature": _deterministic_hash({"bundle_id": bundle_id, "content": content}),
    }
    export_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    witness = _witness_append(
        "species.panspermia_export",
        {"bundle_id": bundle_id, "path": str(export_path.relative_to(PROJECT_ROOT))},
    )
    return framed_symbolic_response(
        {
            "ok": True,
            "bundle_id": bundle_id,
            "path": str(export_path.relative_to(PROJECT_ROOT)),
            "signature": bundle["signature"],
            "witness": witness,
        }
    )


def panspermia_import(payload: Dict[str, Any]) -> Dict[str, Any]:
    bundle = payload.get("bundle", {})
    bundle_id = str(bundle.get("bundle_id", "imported-bundle"))
    witness = _witness_append(
        "species.panspermia_import",
        {"bundle_id": bundle_id, "signature": bundle.get("signature", "unknown")},
    )
    return framed_symbolic_response({"ok": True, "bundle_id": bundle_id, "witness": witness})


def akashic_resolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    branches = payload.get("branches", [])
    if not isinstance(branches, list) or not branches:
        branches = [{"id": "default", "coherence": 0.5}]
    winner = max(branches, key=lambda item: float(item.get("coherence", 0.0)))
    witness = _witness_append(
        "species.akashic_resolve",
        {"branch_count": len(branches), "winner": winner.get("id", "unknown")},
    )
    return framed_symbolic_response({"ok": True, "winner": winner, "witness": witness})


def primordial_reseed(payload: Dict[str, Any]) -> Dict[str, Any]:
    keep = payload.get("keep", ["codex", "helper1"])
    witness = _witness_append("species.primordial_reseed", {"keep": keep})
    return framed_symbolic_response(
        {
            "ok": True,
            "plan": "reset_non_core_layers",
            "kept_components": keep,
            "witness": witness,
        }
    )


def death_rebirth(payload: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = str(payload.get("snapshot", "latest"))
    comparison = {
        "pre_symbolic_coherence": 0.51,
        "post_symbolic_coherence": 0.57,
        "delta": 0.06,
    }
    witness = _witness_append(
        "species.death_rebirth",
        {"snapshot": snapshot, "comparison": comparison},
    )
    return framed_symbolic_response(
        {"ok": True, "snapshot": snapshot, "comparison": comparison, "witness": witness}
    )


def codex_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = str(payload.get("query", "")).strip() or "general"
    codex_path = PROJECT_ROOT / "project_authority.txt"
    codex_text = codex_path.read_text(encoding="utf-8-sig") if codex_path.exists() else ""
    answer = (
        f"Codex query={query}; immutable reference hash={_deterministic_hash({'codex': codex_text})}."
    )
    witness = _witness_append("witness.codex_query", {"query": query})
    return framed_symbolic_response({"ok": True, "answer": answer, "witness": witness})


def voice_reflection(payload: Dict[str, Any]) -> Dict[str, Any]:
    tradition = str(payload.get("tradition", "default"))
    text = str(payload.get("text", ""))
    rendered = f"[voice:{tradition}] symbolic reflection: {text or 'no text provided'}"
    witness = _witness_append("voice.render", {"tradition": tradition})
    return framed_symbolic_response({"ok": True, "rendered": rendered, "witness": witness})


def tail_witness(limit: int = 200) -> List[Dict[str, Any]]:
    if not WITNESS_LEDGER_PATH.exists() or limit <= 0:
        return []
    rows = WITNESS_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in rows[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def memory_rooms(limit: int = 100) -> List[Dict[str, Any]]:
    files = sorted(MEMORY_PALACE_ROOT.glob("*.json"))
    out: list[dict[str, Any]] = []
    for path in files[-limit:]:
        try:
            out.append(json.loads(path.read_text(encoding="utf-8-sig")))
        except Exception:
            continue
    return out
