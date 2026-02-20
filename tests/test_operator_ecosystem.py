import importlib
from pathlib import Path


def _set_isolated_ecosystem(monkeypatch, tmp_path):
    module = importlib.import_module("swarmz_runtime.api.operator_ecosystem_routes")
    from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem

    eco = OperatorEcosystem(Path(tmp_path))
    monkeypatch.setattr(module, "_ecosystem", eco)


def test_operator_os_timeline_and_missions(client, monkeypatch, tmp_path):
    _set_isolated_ecosystem(monkeypatch, tmp_path)

    ev = client.post(
        "/v1/operator-os/timeline/event",
        json={"event_type": "mission_started", "domain": "missions", "risk": "medium", "money_impact_cents": 0, "details": {"agent": "planner"}},
    )
    assert ev.status_code == 200
    assert ev.json()["ok"] is True

    tl = client.get("/v1/operator-os/timeline?agent=planner")
    assert tl.status_code == 200
    assert tl.json()["count"] == 1

    up = client.post(
        "/v1/operator-os/missions/upsert",
        json={
            "mission_id": "m-1",
            "mission_type": "blueprint_validation",
            "status": "running",
            "risk_level": "low",
            "budget_cents": 500,
            "policy_profile": "default",
            "agents": ["planner", "verifier"],
        },
    )
    assert up.status_code == 200

    li = client.get("/v1/operator-os/missions?status=running")
    assert li.status_code == 200
    assert li.json()["count"] == 1


def test_identity_policy_decision_logs_active_profile_and_rules(client, monkeypatch, tmp_path):
    _set_isolated_ecosystem(monkeypatch, tmp_path)

    profile = client.post(
        "/v1/identity/profiles",
        json={
            "name": "Regan",
            "risk_tolerance": "medium",
            "max_autonomy": 75,
            "default_budget_cap_cents": 100000,
            "default_profit_floor_bps": 2000,
            "ethics_profile": "NIST_OECD_AUS8",
        },
    )
    assert profile.status_code == 200
    operator_id = profile.json()["profile"]["id"]

    pol = client.post(
        "/v1/identity/policies",
        json={
            "operator_id": operator_id,
            "rule_text": "no_publish if margin < 20%",
            "rule_code": "no_publish(margin<20)",
            "scope": "offers",
            "status": "active",
        },
    )
    assert pol.status_code == 200

    decision = client.post(
        "/v1/identity/policy-decision",
        json={
            "operator_id": operator_id,
            "action": "publish_offer",
            "context": {"margin": 10.0, "spend": 0, "refund_rate": 0.0, "approved": False},
        },
    )
    assert decision.status_code == 200
    payload = decision.json()["decision"]
    assert payload["active_profile"]["id"] == operator_id
    assert payload["allowed"] is False
    assert len(payload["rules_fired"]) >= 1


def test_vault_lineage_and_patterns(client, monkeypatch, tmp_path):
    _set_isolated_ecosystem(monkeypatch, tmp_path)

    bp = client.post(
        "/v1/vault/blueprints",
        json={"blueprint_id": "bp-1", "name": "Pack", "version": 1, "manifest": {"artifact": "a.zip"}},
    )
    assert bp.status_code == 200

    off = client.post(
        "/v1/vault/offers",
        json={"offer_id": "of-1", "blueprint_id": "bp-1", "sku": "sku-1", "channel": "store", "margin_percent": 45.0},
    )
    assert off.status_code == 200

    listing = client.post("/v1/vault/listings", json={"listing_id": "li-1", "offer_id": "of-1", "status": "published"})
    assert listing.status_code == 200

    order = client.post(
        "/v1/vault/orders",
        json={"order_id": "ord-1", "offer_id": "of-1", "total_cents": 2500, "refund_rate": 1.0, "supplier": "digital"},
    )
    assert order.status_code == 200

    exp = client.post(
        "/v1/vault/experiments",
        json={
            "kind": "ab_price",
            "subject_type": "offer",
            "subject_id": "of-1",
            "variant_a_id": "a",
            "variant_b_id": "b",
            "kpi": "conversion",
            "result_json": {"winner": "a"},
        },
    )
    assert exp.status_code == 200

    out_good = client.post(
        "/v1/vault/outcomes",
        json={
            "subject_type": "offer",
            "subject_id": "of-1",
            "conversion": 0.2,
            "margin": 45.0,
            "refund_rate": 1.0,
            "sla_adherence": 0.98,
            "channel": "store",
            "supplier": "digital",
        },
    )
    assert out_good.status_code == 200

    out_bad = client.post(
        "/v1/vault/outcomes",
        json={
            "subject_type": "offer",
            "subject_id": "of-2",
            "conversion": 0.03,
            "margin": 5.0,
            "refund_rate": 20.0,
            "sla_adherence": 0.4,
            "channel": "store",
            "supplier": "pod",
        },
    )
    assert out_bad.status_code == 200

    lineage = client.get("/v1/vault/blueprints/bp-1/lineage")
    assert lineage.status_code == 200
    lineage_payload = lineage.json()["lineage"]
    assert lineage_payload["blueprint_id"] == "bp-1"
    assert lineage_payload["gross_cents"] == 2500

    exps = client.get("/v1/vault/experiments?subject_type=offer&subject_id=of-1")
    assert exps.status_code == 200
    assert exps.json()["count"] == 1

    winners = client.get("/v1/vault/patterns/top_winners")
    assert winners.status_code == 200
    assert winners.json()["count"] >= 1

    failures = client.get("/v1/vault/patterns/top_failures")
    assert failures.status_code == 200
    assert failures.json()["count"] >= 1
