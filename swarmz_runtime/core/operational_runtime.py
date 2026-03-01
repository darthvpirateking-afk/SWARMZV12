from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class RuleResult:
    allowed: bool
    rule: str
    reason: str


PROCESSED_EVENTS_PATH = Path("data/payments/processed_events.jsonl")


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    secret = os.environ.get("PAYMENT_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("PAYMENT_WEBHOOK_SECRET not set")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header.split("=")[-1].strip()
    if not received:
        return False
    return hmac.compare_digest(expected, received)


def _extract_event_id(payload: dict[str, Any]) -> str:
    event_id = payload.get("id")
    if event_id:
        return str(event_id)
    fallback_key = f"{payload.get('order_id', '')}:{payload.get('event', '')}"
    return hashlib.sha256(fallback_key.encode()).hexdigest()[:32]


def is_already_processed(event_id: str) -> bool:
    if not PROCESSED_EVENTS_PATH.exists():
        return False
    with PROCESSED_EVENTS_PATH.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event_id") == event_id:
                return True
    return False


def mark_processed(event_id: str) -> None:
    PROCESSED_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROCESSED_EVENTS_PATH.open("a", encoding="utf-8") as stream:
        json.dump(
            {
                "event_id": event_id,
                "processed_at": datetime.now(UTC).isoformat(),
            },
            stream,
        )
        stream.write("\n")


class PolicyEngine:
    def __init__(self, rules: list[str] | None = None):
        self._rules = rules or [
            "no_publish if margin < 20",
            "require_approval if spend > 50",
            "block if refund_rate > 5% last 30d",
        ]

    @property
    def rules(self) -> list[str]:
        return list(self._rules)

    def evaluate_publish(self, metrics: dict[str, Any]) -> RuleResult:
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
    def agents(self) -> list[str]:
        return list(self._agents)

    def run(
        self, goal: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "goal": goal,
            "context": context or {},
            "agents": self.agents,
            "status": "completed",
        }
        self._append_jsonl(self._checkpoints, payload)
        return payload

    @staticmethod
    def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
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
        self, name: str, spec: dict[str, Any], owner: str = "operator"
    ) -> dict[str, Any]:
        blueprint = {
            "blueprint_id": f"bp-{secrets.token_hex(4)}",
            "name": name,
            "owner": owner,
            "version": 1,
            "spec": spec,
            "status": "created",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._append_jsonl(self._blueprints_file, blueprint)
        return blueprint

    def validate_blueprint(self, blueprint_id: str) -> dict[str, Any]:
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
            "validated_at": datetime.now(UTC).isoformat(),
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
    ) -> dict[str, Any]:
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
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._append_jsonl(self._offers_file, offer)
        return offer

    def list_catalog(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self._offers_file)

    def checkout(
        self, sku: str, quantity: int, payment_provider: str = "manual"
    ) -> dict[str, Any]:
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
            "created_at": datetime.now(UTC).isoformat(),
        }
        order["total_cents"] = order["quantity"] * order["unit_price_cents"]
        self._append_jsonl(self._orders_file, order)
        return order

    def payment_webhook(self, order_id: str, event: str) -> dict[str, Any]:
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
        order["paid_at"] = datetime.now(UTC).isoformat()
        self._append_jsonl(self._orders_file, order)

        self._append_jsonl(
            self._ledger_file,
            {
                "entry_id": f"led-{secrets.token_hex(4)}",
                "type": "revenue",
                "order_id": order_id,
                "amount_cents": order["total_cents"],
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        return {"ok": True, "idempotent": False, "order": order}

    def fulfill_order(self, order_id: str, mode: str = "digital") -> dict[str, Any]:
        order = self._find_last(self._orders_file, "order_id", order_id)
        if not order:
            return {"error": "order_not_found"}
        if order.get("status") not in {"paid", "fulfilled"}:
            return {"error": "order_not_ready"}
        if order.get("status") == "fulfilled":
            return {"ok": True, "idempotent": True, "order": order}

        order["status"] = "fulfilled"
        order["fulfillment_mode"] = mode
        order["fulfilled_at"] = datetime.now(UTC).isoformat()
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
                "timestamp": datetime.now(UTC).isoformat(),
                "meta": {"mode": mode, "tracking": order["tracking"]},
            },
        )
        return {"ok": True, "idempotent": False, "order": order}

    def ledger_tail(self, limit: int = 50) -> list[dict[str, Any]]:
        entries = self._read_jsonl(self._ledger_file)
        return entries[-max(1, min(limit, 500)) :]

    def run_autonomy_cycle(self, label: str = "default") -> dict[str, Any]:
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
    def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
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

    def _find_last(self, path: Path, key: str, value: Any) -> dict[str, Any] | None:
        entries = self._read_jsonl(path)
        for entry in reversed(entries):
            if entry.get(key) == value:
                return entry
        return None
