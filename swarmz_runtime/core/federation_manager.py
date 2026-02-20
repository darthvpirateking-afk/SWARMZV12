from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class FederationManager:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._base = root_dir / "data" / "federation"
        self._base.mkdir(parents=True, exist_ok=True)

        self._organisms = self._base / "organisms.jsonl"
        self._configs = self._base / "organism_configs.jsonl"
        self._policies = self._base / "organism_policies.jsonl"
        self._metrics = self._base / "organism_metrics.jsonl"
        self._insights = self._base / "global_insights.jsonl"

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
    def _latest_by_id(
        rows: List[Dict[str, Any]], key: str = "id"
    ) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if key in row:
                latest[row[key]] = row
        return latest

    def create_organism(
        self, name: str, owner_id: str, config_json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        organism_id = f"org-{secrets.token_hex(4)}"
        organism = {
            "id": organism_id,
            "name": name,
            "owner_id": owner_id,
            "status": "active",
            "created_at": self._now(),
            "partner": {
                "tier": 0,
                "traits": {
                    "logic": 10,
                    "precision": 10,
                    "empathy": 10,
                    "initiative": 10,
                    "stability": 10,
                },
            },
            "shadow": {"tier": "Dormant", "risk_profile": "strict"},
            "autonomy": {"dial": 10},
            "ledger_mode": "isolated",
        }
        self._append_jsonl(self._organisms, organism)

        cfg = {
            "id": f"cfg-{secrets.token_hex(4)}",
            "organism_id": organism_id,
            "config_json": config_json
            or {"mode": "prime", "policy_profile": "default"},
            "created_at": self._now(),
        }
        self._append_jsonl(self._configs, cfg)

        baseline_policy = {
            "id": f"pol-{secrets.token_hex(4)}",
            "organism_id": organism_id,
            "rule_code": "global_safety_baseline",
            "status": "active",
            "created_at": self._now(),
        }
        self._append_jsonl(self._policies, baseline_policy)

        return {
            "organism": organism,
            "config": cfg,
            "policy": baseline_policy,
        }

    def get_organism(self, organism_id: str) -> Optional[Dict[str, Any]]:
        latest = self._latest_by_id(self._read_jsonl(self._organisms))
        return latest.get(organism_id)

    def list_organisms(self) -> List[Dict[str, Any]]:
        latest = self._latest_by_id(self._read_jsonl(self._organisms))
        return list(latest.values())

    def pause_organism(
        self, organism_id: str, reason: str = "operator_command"
    ) -> Optional[Dict[str, Any]]:
        organism = self.get_organism(organism_id)
        if not organism:
            return None
        organism = {
            **organism,
            "status": "paused",
            "paused_reason": reason,
            "updated_at": self._now(),
        }
        self._append_jsonl(self._organisms, organism)
        return organism

    def retire_organism(
        self, organism_id: str, reason: str = "operator_retire"
    ) -> Optional[Dict[str, Any]]:
        organism = self.get_organism(organism_id)
        if not organism:
            return None
        organism = {
            **organism,
            "status": "retired",
            "retired_reason": reason,
            "updated_at": self._now(),
        }
        self._append_jsonl(self._organisms, organism)
        return organism

    def evolve_organism(
        self,
        organism_id: str,
        mission_success: bool,
        incidents: int,
        policy_compliance: bool,
    ) -> Optional[Dict[str, Any]]:
        organism = self.get_organism(organism_id)
        if not organism:
            return None
        if organism.get("status") != "active":
            return organism

        partner = dict(organism.get("partner", {}))
        tier = int(partner.get("tier", 0))
        autonomy = int(organism.get("autonomy", {}).get("dial", 10))

        if mission_success and incidents == 0 and policy_compliance:
            tier = min(5, tier + 1)
            autonomy = min(100, autonomy + 10)
        else:
            autonomy = max(0, autonomy - 10)

        partner["tier"] = tier
        organism["partner"] = partner
        organism["autonomy"] = {"dial": autonomy}
        organism["updated_at"] = self._now()
        self._append_jsonl(self._organisms, organism)

        self._append_jsonl(
            self._metrics,
            {
                "id": f"met-{secrets.token_hex(4)}",
                "organism_id": organism_id,
                "metrics_json": {
                    "partner_tier": tier,
                    "autonomy_dial": autonomy,
                    "mission_success": mission_success,
                    "incidents": incidents,
                    "policy_compliance": policy_compliance,
                },
                "ts": self._now(),
            },
        )
        return organism

    def aggregate_metrics(self) -> Dict[str, Any]:
        organisms = self.list_organisms()
        metrics = self._read_jsonl(self._metrics)

        active = sum(1 for o in organisms if o.get("status") == "active")
        paused = sum(1 for o in organisms if o.get("status") == "paused")
        retired = sum(1 for o in organisms if o.get("status") == "retired")

        avg_autonomy = 0.0
        if organisms:
            avg_autonomy = sum(
                float(o.get("autonomy", {}).get("dial", 0)) for o in organisms
            ) / len(organisms)

        return {
            "organism_count": len(organisms),
            "active": active,
            "paused": paused,
            "retired": retired,
            "average_autonomy_dial": round(avg_autonomy, 2),
            "metric_events": len(metrics),
        }

    def generate_nightly_insights(
        self, outcomes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        rows = outcomes or []
        winners = sorted(
            rows,
            key=lambda r: (
                float(r.get("margin", 0.0)),
                float(r.get("conversion", 0.0)),
            ),
            reverse=True,
        )[:5]
        failures = sorted(
            rows,
            key=lambda r: (
                float(r.get("refund_rate", 0.0)),
                -float(r.get("sla_adherence", 0.0)),
            ),
            reverse=True,
        )[:5]

        insight = {
            "id": f"ins-{secrets.token_hex(4)}",
            "generated_at": self._now(),
            "safe_insights": [
                {
                    "type": "winner_pattern",
                    "subject_id": w.get("subject_id"),
                    "suggestion": "test +5-10% price band",
                }
                for w in winners
            ],
            "safe_warnings": [
                {
                    "type": "failure_pattern",
                    "subject_id": f.get("subject_id"),
                    "warning": "high refund-risk pattern",
                }
                for f in failures
            ],
            "privacy_mode": "no_customer_data",
        }
        self._append_jsonl(self._insights, insight)
        return insight

    def latest_insights(self) -> Optional[Dict[str, Any]]:
        rows = self._read_jsonl(self._insights)
        return rows[-1] if rows else None
