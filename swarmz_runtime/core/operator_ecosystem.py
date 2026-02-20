from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperatorEcosystem:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._base = root_dir / "data" / "operator_ecosystem"
        self._base.mkdir(parents=True, exist_ok=True)

        self._events = self._base / "events.jsonl"
        self._missions = self._base / "missions.jsonl"
        self._risk = self._base / "money_risk.jsonl"
        self._decisions = self._base / "policy_decisions.jsonl"

        self._profiles = self._base / "operator_profiles.jsonl"
        self._preferences = self._base / "operator_preferences.jsonl"
        self._policies = self._base / "operator_policies.jsonl"
        self._goals = self._base / "operator_goals.jsonl"

        self._blueprints = self._base / "blueprints.jsonl"
        self._offers = self._base / "offers.jsonl"
        self._listings = self._base / "listings.jsonl"
        self._orders = self._base / "orders.jsonl"
        self._experiments = self._base / "experiments.jsonl"
        self._outcomes = self._base / "outcomes.jsonl"
        self._reflections = self._base / "reflections.jsonl"
        self._embeddings = self._base / "embeddings.jsonl"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows

    @staticmethod
    def _find_last(rows: List[Dict[str, Any]], key: str, value: Any) -> Optional[Dict[str, Any]]:
        for row in reversed(rows):
            if row.get(key) == value:
                return row
        return None

    # ---------- Operator OS ----------
    def add_event(self, event_type: str, domain: str, risk: str = "low", money_impact_cents: int = 0, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        row = {
            "event_id": f"evt-{secrets.token_hex(4)}",
            "event_type": event_type,
            "domain": domain,
            "risk": risk,
            "money_impact_cents": int(money_impact_cents),
            "details": details or {},
            "created_at": self._now(),
        }
        self._append_jsonl(self._events, row)
        return row

    def list_timeline(self, agent: Optional[str] = None, domain: Optional[str] = None, risk: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._events)
        if agent:
            rows = [r for r in rows if str(r.get("details", {}).get("agent", "")).lower() == agent.lower()]
        if domain:
            rows = [r for r in rows if str(r.get("domain", "")).lower() == domain.lower()]
        if risk:
            rows = [r for r in rows if str(r.get("risk", "")).lower() == risk.lower()]
        return rows

    def upsert_mission(self, mission_id: str, mission_type: str, status: str, risk_level: str, budget_cents: int, policy_profile: str, agents: List[str]) -> Dict[str, Any]:
        row = {
            "mission_id": mission_id,
            "mission_type": mission_type,
            "status": status,
            "risk_level": risk_level,
            "budget_cents": int(budget_cents),
            "policy_profile": policy_profile,
            "agents": agents,
            "updated_at": self._now(),
        }
        self._append_jsonl(self._missions, row)
        return row

    def list_missions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._missions)
        latest: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            latest[row["mission_id"]] = row
        out = list(latest.values())
        if status:
            out = [r for r in out if str(r.get("status", "")).lower() == status.lower()]
        return out

    def set_money_risk_snapshot(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = {"snapshot_id": f"mr-{secrets.token_hex(4)}", "created_at": self._now(), **payload}
        self._append_jsonl(self._risk, row)
        return row

    # ---------- Operator Identity ----------
    def create_operator_profile(
        self,
        name: str,
        risk_tolerance: str,
        max_autonomy: int,
        default_budget_cap_cents: int,
        default_profit_floor_bps: int,
        ethics_profile: str,
    ) -> Dict[str, Any]:
        row = {
            "id": f"op-{secrets.token_hex(4)}",
            "name": name,
            "risk_tolerance": risk_tolerance,
            "max_autonomy": max(0, min(100, int(max_autonomy))),
            "default_budget_cap_cents": int(default_budget_cap_cents),
            "default_profit_floor_bps": int(default_profit_floor_bps),
            "ethics_profile": ethics_profile,
            "created_at": self._now(),
        }
        self._append_jsonl(self._profiles, row)
        return row

    def list_operator_profiles(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self._profiles)

    def add_preference(self, operator_id: str, key: str, value_json: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": f"pref-{secrets.token_hex(4)}",
            "operator_id": operator_id,
            "key": key,
            "value_json": value_json,
            "created_at": self._now(),
        }
        self._append_jsonl(self._preferences, row)
        return row

    def add_policy(self, operator_id: str, rule_text: str, rule_code: str, scope: str, status: str = "active") -> Dict[str, Any]:
        row = {
            "id": f"pol-{secrets.token_hex(4)}",
            "operator_id": operator_id,
            "rule_text": rule_text,
            "rule_code": rule_code,
            "scope": scope,
            "status": status,
            "created_at": self._now(),
        }
        self._append_jsonl(self._policies, row)
        return row

    def add_goal(self, operator_id: str, time_horizon: str, goal_text: str, metrics_json: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": f"goal-{secrets.token_hex(4)}",
            "operator_id": operator_id,
            "time_horizon": time_horizon,
            "goal_text": goal_text,
            "metrics_json": metrics_json,
            "created_at": self._now(),
        }
        self._append_jsonl(self._goals, row)
        return row

    def evaluate_policy_decision(self, operator_id: str, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        profiles = self._read_jsonl(self._profiles)
        profile = self._find_last(profiles, "id", operator_id)
        if not profile:
            return {"error": "operator_not_found"}

        policies = [p for p in self._read_jsonl(self._policies) if p.get("operator_id") == operator_id and p.get("status") == "active"]
        fired: List[str] = []
        allowed = True

        margin = float(context.get("margin", 100.0))
        spend = float(context.get("spend", 0.0))
        refund_rate = float(context.get("refund_rate", 0.0))

        for p in policies:
            txt = p.get("rule_text", "").lower()
            if "margin < 20" in txt and margin < 20.0:
                fired.append(p["id"])
                allowed = False
            if "spend > 100" in txt and spend > 100.0 and not context.get("approved", False):
                fired.append(p["id"])
                allowed = False
            if "refund_rate > 5" in txt and refund_rate > 5.0:
                fired.append(p["id"])
                allowed = False

        decision = {
            "decision_id": f"dec-{secrets.token_hex(4)}",
            "operator_id": operator_id,
            "action": action,
            "allowed": allowed,
            "active_profile": {
                "id": profile["id"],
                "risk_tolerance": profile.get("risk_tolerance"),
                "max_autonomy": profile.get("max_autonomy"),
                "ethics_profile": profile.get("ethics_profile"),
            },
            "rules_fired": fired,
            "context": context,
            "created_at": self._now(),
        }
        self._append_jsonl(self._decisions, decision)
        return decision

    # ---------- Artifact Vault ----------
    def add_blueprint(self, blueprint_id: str, name: str, version: int, manifest: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "blueprint_id": blueprint_id,
            "name": name,
            "version": int(version),
            "manifest": manifest,
            "created_at": self._now(),
        }
        self._append_jsonl(self._blueprints, row)
        return row

    def add_offer(self, offer_id: str, blueprint_id: str, sku: str, channel: str, margin_percent: float) -> Dict[str, Any]:
        row = {
            "offer_id": offer_id,
            "blueprint_id": blueprint_id,
            "sku": sku,
            "channel": channel,
            "margin_percent": float(margin_percent),
            "created_at": self._now(),
        }
        self._append_jsonl(self._offers, row)
        return row

    def add_listing(self, listing_id: str, offer_id: str, status: str) -> Dict[str, Any]:
        row = {"listing_id": listing_id, "offer_id": offer_id, "status": status, "created_at": self._now()}
        self._append_jsonl(self._listings, row)
        return row

    def add_order(self, order_id: str, offer_id: str, total_cents: int, refund_rate: float, supplier: str) -> Dict[str, Any]:
        row = {
            "order_id": order_id,
            "offer_id": offer_id,
            "total_cents": int(total_cents),
            "refund_rate": float(refund_rate),
            "supplier": supplier,
            "created_at": self._now(),
        }
        self._append_jsonl(self._orders, row)
        return row

    def add_experiment(
        self,
        kind: str,
        subject_type: str,
        subject_id: str,
        variant_a_id: str,
        variant_b_id: str,
        kpi: str,
        result_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        row = {
            "id": f"exp-{secrets.token_hex(4)}",
            "kind": kind,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "variant_a_id": variant_a_id,
            "variant_b_id": variant_b_id,
            "kpi": kpi,
            "result_json": result_json,
            "started_at": self._now(),
            "ended_at": self._now(),
        }
        self._append_jsonl(self._experiments, row)
        return row

    def add_outcome(self, subject_type: str, subject_id: str, conversion: float, margin: float, refund_rate: float, sla_adherence: float, channel: str, supplier: str) -> Dict[str, Any]:
        row = {
            "id": f"out-{secrets.token_hex(4)}",
            "subject_type": subject_type,
            "subject_id": subject_id,
            "conversion": float(conversion),
            "margin": float(margin),
            "refund_rate": float(refund_rate),
            "sla_adherence": float(sla_adherence),
            "channel": channel,
            "supplier": supplier,
            "created_at": self._now(),
        }
        self._append_jsonl(self._outcomes, row)
        return row

    def add_reflection(self, agent: str, scope: str, input_summary: str, output_summary: str, changes_json: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": f"ref-{secrets.token_hex(4)}",
            "agent": agent,
            "scope": scope,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "changes_json": changes_json,
            "created_at": self._now(),
        }
        self._append_jsonl(self._reflections, row)
        return row

    def add_embedding(self, source_type: str, source_id: str, text: str, embedding: List[float]) -> Dict[str, Any]:
        row = {
            "id": f"emb-{secrets.token_hex(4)}",
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "embedding": embedding,
            "created_at": self._now(),
        }
        self._append_jsonl(self._embeddings, row)
        return row

    def get_lineage(self, blueprint_id: str) -> Dict[str, Any]:
        blueprints = [b for b in self._read_jsonl(self._blueprints) if b.get("blueprint_id") == blueprint_id]
        offers = [o for o in self._read_jsonl(self._offers) if o.get("blueprint_id") == blueprint_id]
        offer_ids = {o.get("offer_id") for o in offers}
        listings = [l for l in self._read_jsonl(self._listings) if l.get("offer_id") in offer_ids]
        orders = [o for o in self._read_jsonl(self._orders) if o.get("offer_id") in offer_ids]
        gross_cents = sum(int(o.get("total_cents", 0)) for o in orders)

        return {
            "blueprint_id": blueprint_id,
            "versions": blueprints,
            "offers": offers,
            "listings": listings,
            "orders": orders,
            "gross_cents": gross_cents,
        }

    def list_experiments(self, subject_type: Optional[str] = None, subject_id: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._experiments)
        if subject_type:
            rows = [r for r in rows if str(r.get("subject_type", "")).lower() == subject_type.lower()]
        if subject_id:
            rows = [r for r in rows if str(r.get("subject_id", "")).lower() == subject_id.lower()]
        return rows

    def top_winners(self, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._outcomes)
        rows.sort(key=lambda r: (float(r.get("margin", 0.0)), float(r.get("conversion", 0.0))), reverse=True)
        return rows[: max(1, limit)]

    def top_failures(self, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._outcomes)
        rows.sort(key=lambda r: (float(r.get("refund_rate", 0.0)), -float(r.get("sla_adherence", 0.0))), reverse=True)
        return rows[: max(1, limit)]
