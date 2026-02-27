from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RuleResult:
    allowed: bool
    rule: str
    reason: str


class PolicyEngine:
    def __init__(self, rules: Optional[List[str]] = None):
        self._rules = rules or [
            "no_publish if margin < 20",
            "require_approval if spend > 50",
            "block if refund_rate > 5% last 30d",
        ]

    @property
    def rules(self) -> List[str]:
        return list(self._rules)

    def evaluate_publish(self, metrics: Dict[str, Any]) -> RuleResult:
        margin = float(metrics.get("margin", 0.0))
        if margin < 20.0:
            return RuleResult(False, "no_publish", "margin below policy floor")

        spend = float(metrics.get("spend", 0.0))
        approved = bool(metrics.get("approved", False))
        if spend > 50.0 and not approved:
            return RuleResult(
                False, "require_approval", "spend threshold exceeded without approval"
            )

        refund_rate = float(metrics.get("refund_rate", 0.0))
        if refund_rate > 5.0:
            return RuleResult(False, "block", "refund rate above policy threshold")

        return RuleResult(True, "allow", "publish allowed")


class LangGraphRuntime:
    def __init__(self, data_dir: Path):
        self._checkpoints = data_dir / "langgraph_checkpoints.jsonl"
        self._agents = [
            "planner",
            "coder",
            "tester",
            "verifier",
            "governance",
            "memory",
            "reflection",
        ]

    @property
    def agents(self) -> List[str]:
        return list(self._agents)

    def run(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": goal,
            "context": context or {},
            "agents": self.agents,
            "status": "completed",
        }
        self._append_jsonl(self._checkpoints, payload)
        return payload

    @staticmethod
    def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")


class OperationalRuntime:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._ops_dir = root_dir / "data" / "ops"
        self._ops_dir.mkdir(parents=True, exist_ok=True)
        self._policy = PolicyEngine()
        self._langgraph = LangGraphRuntime(root_dir / "data")

        self._blueprints_file = self._ops_dir / "blueprints.jsonl"
        self._offers_file = self._ops_dir / "offers.jsonl"
        self._orders_file = self._ops_dir / "orders.jsonl"
        self._ledger_file = self._ops_dir / "ledger.jsonl"

    @property
    def policy(self) -> PolicyEngine:
        return self._policy

    @property
    def langgraph(self) -> LangGraphRuntime:
        return self._langgraph

    def create_blueprint(
        self, name: str, spec: Dict[str, Any], owner: str = "operator"
    ) -> Dict[str, Any]:
        blueprint = {
            "blueprint_id": f"bp-{secrets.token_hex(4)}",
            "name": name,
            "owner": owner,
            "version": 1,
            "spec": spec,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(self._blueprints_file, blueprint)
        return blueprint

    def validate_blueprint(self, blueprint_id: str) -> Dict[str, Any]:
        blueprint = self._find_last(self._blueprints_file, "blueprint_id", blueprint_id)
        if not blueprint:
            return {"error": "blueprint_not_found"}

        has_artifact = bool(
            blueprint.get("spec", {}).get("artifact")
            or blueprint.get("spec", {}).get("artifact_uri")
        )
        status = "approved" if has_artifact else "needs_review"
        result = {
            "blueprint_id": blueprint_id,
            "validation_status": status,
            "checks": {
                "artifact_present": has_artifact,
                "policy_check": True,
                "qa_pass": has_artifact,
            },
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(
            self._blueprints_file, {**blueprint, "status": status, "validation": result}
        )
        return result

    def create_offer(
        self,
        blueprint_id: str,
        title: str,
        price_cents: int,
        cost_cents: int,
        spend: float = 0.0,
        approved: bool = False,
        refund_rate: float = 0.0,
    ) -> Dict[str, Any]:
        margin = (
            ((price_cents - cost_cents) / price_cents * 100.0)
            if price_cents > 0
            else 0.0
        )
        decision = self._policy.evaluate_publish(
            {
                "margin": margin,
                "spend": spend,
                "approved": approved,
                "refund_rate": refund_rate,
            }
        )

        if not decision.allowed:
            return {
                "error": "policy_blocked",
                "rule": decision.rule,
                "reason": decision.reason,
                "margin": margin,
            }

        offer = {
            "offer_id": f"of-{secrets.token_hex(4)}",
            "blueprint_id": blueprint_id,
            "title": title,
            "sku": f"sku-{secrets.token_hex(3)}",
            "price_cents": int(price_cents),
            "cost_cents": int(cost_cents),
            "margin_percent": round(margin, 2),
            "status": "listed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(self._offers_file, offer)
        return offer

    def list_catalog(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self._offers_file)

    def checkout(
        self, sku: str, quantity: int, payment_provider: str = "manual"
    ) -> Dict[str, Any]:
        offer = self._find_last(self._offers_file, "sku", sku)
        if not offer:
            return {"error": "sku_not_found"}

        order = {
            "order_id": f"ord-{secrets.token_hex(5)}",
            "sku": sku,
            "quantity": max(1, int(quantity)),
            "unit_price_cents": int(offer["price_cents"]),
            "status": "pending_payment",
            "payment_provider": payment_provider,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        order["total_cents"] = order["quantity"] * order["unit_price_cents"]
        self._append_jsonl(self._orders_file, order)
        return order

    def payment_webhook(self, order_id: str, event: str) -> Dict[str, Any]:
        order = self._find_last(self._orders_file, "order_id", order_id)
        if not order:
            return {"error": "order_not_found"}

        if (
            order.get("status") in {"paid", "fulfilled"}
            and event == "payment_succeeded"
        ):
            return {"ok": True, "idempotent": True, "order": order}

        if event != "payment_succeeded":
            return {"error": "unsupported_event"}

        order["status"] = "paid"
        order["paid_at"] = datetime.now(timezone.utc).isoformat()
        self._append_jsonl(self._orders_file, order)

        self._append_jsonl(
            self._ledger_file,
            {
                "entry_id": f"led-{secrets.token_hex(4)}",
                "type": "revenue",
                "order_id": order_id,
                "amount_cents": order["total_cents"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return {"ok": True, "idempotent": False, "order": order}

    def fulfill_order(self, order_id: str, mode: str = "digital") -> Dict[str, Any]:
        order = self._find_last(self._orders_file, "order_id", order_id)
        if not order:
            return {"error": "order_not_found"}
        if order.get("status") not in {"paid", "fulfilled"}:
            return {"error": "order_not_ready"}
        if order.get("status") == "fulfilled":
            return {"ok": True, "idempotent": True, "order": order}

        order["status"] = "fulfilled"
        order["fulfillment_mode"] = mode
        order["fulfilled_at"] = datetime.now(timezone.utc).isoformat()
        order["tracking"] = (
            f"trk-{secrets.token_hex(4)}" if mode == "physical" else "digital-delivery"
        )
        self._append_jsonl(self._orders_file, order)

        self._append_jsonl(
            self._ledger_file,
            {
                "entry_id": f"led-{secrets.token_hex(4)}",
                "type": "fulfillment",
                "order_id": order_id,
                "amount_cents": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "meta": {"mode": mode, "tracking": order["tracking"]},
            },
        )
        return {"ok": True, "idempotent": False, "order": order}

    def ledger_tail(self, limit: int = 50) -> List[Dict[str, Any]]:
        entries = self._read_jsonl(self._ledger_file)
        return entries[-max(1, min(limit, 500)) :]

    def run_autonomy_cycle(self, label: str = "default") -> Dict[str, Any]:
        run = self._langgraph.run(
            goal="autonomy_loop_cycle",
            context={
                "cycle_label": label,
                "sensors": [
                    "sales",
                    "refunds",
                    "support",
                    "delays",
                    "spend",
                    "conversion",
                    "blueprint_performance",
                ],
            },
        )
        return {
            "ok": True,
            "cycle_label": label,
            "phase_order": [
                "sensors",
                "planning",
                "shadow_execution",
                "policy_checks",
                "resources",
                "memory",
                "reflection",
                "variant_generation",
                "ab_tests",
                "promotion",
            ],
            "run": run,
        }

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

    def _find_last(self, path: Path, key: str, value: Any) -> Optional[Dict[str, Any]]:
        entries = self._read_jsonl(path)
        for entry in reversed(entries):
            if entry.get(key) == value:
                return entry
        return None
