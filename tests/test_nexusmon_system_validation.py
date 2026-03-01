from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import create_app

client = TestClient(create_app())
HEADERS = {"X-Operator-Approval": "true"}


def _governed(payload: dict) -> dict:
    return {
        **payload,
        "ritual_confirmation": {"confirmed": True, "source": "pytest"},
    }


def test_life_endpoints_validation_matrix() -> None:
    # Diary cadence
    res = client.post(
        "/v1/nexusmon/life/diary/tick",
        json=_governed(
            {
                "active_layers": ["symbolic", "life"],
                "routing_imbalance": "balanced",
                "operator_actions": ["approve"],
                "anomalies": [],
                "optimization_goals": ["stability"],
                "recent_missions": ["m1"],
            }
        ),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "entry_path" in res.json()

    # Awakening loop proposals
    res = client.post(
        "/v1/nexusmon/life/awakening/tick",
        json=_governed({"active_layers": ["pantheon"]}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "meta_proposals" in res.json()

    # Breath inhale/exhale
    res = client.post(
        "/v1/nexusmon/life/breath/cycle",
        json=_governed({"phase": "inhale"}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["breath"]["phase"] == "inhale"
    res = client.post(
        "/v1/nexusmon/life/breath/cycle",
        json=_governed({"phase": "exhale"}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["breath"]["phase"] == "exhale"

    # Heart BPM influence
    res = client.post(
        "/v1/nexusmon/life/heart/pulse",
        json=_governed({"swarm_health": 0.9}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "bpm" in res.json()["heart"]

    # Memory palace room generation
    res = client.post(
        "/v1/nexusmon/life/memory_palace/build",
        json=_governed({"mission_id": "validation-mission", "archetypes": ["operator"]}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "room_path" in res.json()

    # Guardian recursion kill switch
    res = client.post(
        "/v1/nexusmon/life/guardians/infinite_regress/check",
        json=_governed({"depth": 12, "limit": 5}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["terminated"] is True

    # Dream seed interpretation
    res = client.post(
        "/v1/nexusmon/life/dream_seed/interpret",
        json=_governed({"seed": {"motif": "bridge"}}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "proposals" in res.json()

    # Sovereign mirror analysis
    res = client.post(
        "/v1/nexusmon/life/sovereign_mirror/reflect",
        json=_governed({"approvals": 3, "rejections": 1, "cockpit_interactions": 5}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "summary" in res.json()

    # Cosmic/noetic triggers
    res = client.post(
        "/v1/nexusmon/life/cosmic/dark_pool",
        json=_governed({"death_states": 3}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["triggered"] is True
    res = client.post(
        "/v1/nexusmon/life/cosmic/zero_point",
        json=_governed({"entropy": 0.7}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "micro_bias" in res.json()
    res = client.post(
        "/v1/nexusmon/life/cosmic/eclipse_alignment",
        json=_governed({"event": "eclipse"}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "mode" in res.json()
    res = client.post(
        "/v1/nexusmon/life/cosmic/noetic_resonance",
        json=_governed({"pattern_spike": 0.91}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["amplified"] is True

    # Species-level export/import + forks
    export = client.post(
        "/v1/nexusmon/life/species/panspermia/export",
        json=_governed({"bundle_id": "v-test"}),
        headers=HEADERS,
    )
    assert export.status_code == 200
    bundle = {"bundle_id": export.json()["bundle_id"], "signature": export.json()["signature"]}
    imported = client.post(
        "/v1/nexusmon/life/species/panspermia/import",
        json=_governed({"bundle": bundle}),
        headers=HEADERS,
    )
    assert imported.status_code == 200
    fork = client.post(
        "/v1/nexusmon/life/species/akashic_resolve",
        json=_governed({"branches": [{"id": "a", "coherence": 0.4}, {"id": "b", "coherence": 0.8}]}),
        headers=HEADERS,
    )
    assert fork.status_code == 200
    assert fork.json()["winner"]["id"] == "b"

    # Primordial + death/rebirth
    res = client.post(
        "/v1/nexusmon/life/species/primordial_reseed",
        json=_governed({"keep": ["codex", "helper1"]}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    rebirth = client.post(
        "/v1/nexusmon/life/species/death_rebirth",
        json=_governed({"snapshot": "latest"}),
        headers=HEADERS,
    )
    assert rebirth.status_code == 200
    assert "comparison" in rebirth.json()

    # Codex lock and voice
    res = client.post(
        "/v1/nexusmon/life/witness/codex_query",
        json=_governed({"query": "sovereignty"}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "answer" in res.json()
    res = client.post(
        "/v1/nexusmon/life/voice/speak",
        json=_governed({"tradition": "norse", "text": "symbolic signal"}),
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "rendered" in res.json()


def test_symbolic_hook_endpoints_matrix() -> None:
    # Pantheon invocation, grimoire consult, sigil geometry, anomaly + branch, etc.
    matrix = [
        ("/v1/nexusmon/symbolic/invoke", {"family": "pantheons"}),
        ("/v1/nexusmon/symbolic/consult", {"family": "grimoires"}),
        ("/v1/nexusmon/symbolic/interpret", {"family": "pantheons"}),
        ("/v1/nexusmon/symbolic/geometry", {"family": "sigils"}),
        ("/v1/nexusmon/symbolic/anomaly", {"family": "cryptids"}),
        ("/v1/nexusmon/symbolic/correspondence", {"family": "reconciliation"}),
        ("/v1/nexusmon/symbolic/altar", {"family": "altar_modes"}),
        ("/v1/nexusmon/symbolic/branch", {"family": "multiverse"}),
    ]
    for endpoint, payload in matrix:
        res = client.post(
            endpoint,
            json=_governed({**payload, "context": endpoint}),
            headers=HEADERS,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["symbolic_only"] is True
        assert body["non_supernatural"] is True

    # Federation, lost civilization, time echo inventory browsable
    res = client.get("/v1/nexusmon/symbolic/families/federation/entries")
    assert res.status_code == 200
    res = client.get("/v1/nexusmon/symbolic/families/lost_civilizations/entries")
    assert res.status_code == 200
    res = client.get("/v1/nexusmon/symbolic/families/archives/entries")
    assert res.status_code == 200


def test_phase12_to_14_endpoints_still_wired() -> None:
    # Planner
    created = client.post("/v1/nexusmon/plans")
    assert created.status_code == 200
    plan_id = created.json()["id"]
    listed = client.get("/v1/nexusmon/plans")
    assert listed.status_code == 200
    realized = client.post(f"/v1/nexusmon/plans/{plan_id}/realize")
    assert realized.status_code == 200

    # Refactor hints
    hints = client.get("/v1/nexusmon/refactor/hints")
    assert hints.status_code == 200
    assert isinstance(hints.json(), list)

    # Proposal + simulate
    proposal = client.post(
        "/v1/nexusmon/proposals",
        json={
            "type": "test",
            "risk": "low",
            "title": "simulation validation",
            "rationale": "ensure simulation endpoint works",
            "diff": {"kind": "file", "content_hint": "Add regression test"},
            "created_by": "pytest",
        },
    )
    assert proposal.status_code == 200
    pid = proposal.json()["id"]
    sim = client.get(f"/v1/nexusmon/proposals/{pid}/simulate")
    assert sim.status_code == 200
    assert "summary" in sim.json()

    council = client.get(f"/v1/nexusmon/proposals/{pid}/council")
    assert council.status_code == 200
    assert "consensus" in council.json()
