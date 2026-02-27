import swarmz_runtime.api.server as runtime_server


def test_command_center_state_shape(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    response = client.get("/v1/command-center/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["ok"] is True
    assert "cockpit" in payload
    assert "autonomy" in payload
    assert "shadow_mode" in payload
    assert "evolution_tree" in payload
    assert "marketplace" in payload


def test_set_autonomy_updates_mode(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    response = client.post("/v1/command-center/autonomy", json={"level": 90})
    assert response.status_code == 200
    payload = response.json()

    assert payload["ok"] is True
    assert payload["autonomy"]["requested_level"] == 90
    assert payload["autonomy"]["level"] == 25
    assert payload["autonomy"]["mode"] == "assisted"


def test_shadow_mode_toggle(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    response = client.post(
        "/v1/command-center/shadow", json={"enabled": True, "lane": "sim"}
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["ok"] is True
    assert payload["shadow_mode"]["enabled"] is True
    assert payload["shadow_mode"]["lane"] == "sim"


def test_evolution_promote_partner(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    response = client.post(
        "/v1/command-center/evolution/promote",
        json={"partner_id": "gamma", "reason": "test_promote"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["ok"] is True
    assert payload["partner"]["partner_id"] == "gamma"
    assert payload["partner"]["tier"] in {"scout", "operator", "architect", "sovereign"}


def test_marketplace_publish_and_list(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    publish = client.post(
        "/v1/command-center/marketplace/publish",
        json={
            "mission_type": "analysis",
            "title": "Analyze mission drift",
            "reward_points": 120,
            "tags": ["ops"],
        },
    )
    assert publish.status_code == 200
    publish_payload = publish.json()
    assert publish_payload["ok"] is True
    assert publish_payload["listing"]["mission_type"] == "analysis"

    listed = client.get("/v1/command-center/marketplace/list")
    assert listed.status_code == 200
    listed_payload = listed.json()
    assert listed_payload["ok"] is True
    assert listed_payload["count"] >= 1


def test_organism_state_and_evolution(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    state_before = client.get("/v1/command-center/organism/state")
    assert state_before.status_code == 200
    before_payload = state_before.json()
    assert before_payload["ok"] is True
    assert before_payload["partner"]["tier"] == "Rookie"
    assert before_payload["shadow"]["tier"] == "Dormant"

    evolve_partner = client.post(
        "/v1/command-center/partner/evolve", json={"reason": "mission_success"}
    )
    assert evolve_partner.status_code == 200
    partner_payload = evolve_partner.json()
    assert partner_payload["ok"] is True
    assert partner_payload["partner"]["tier"] == "Champion"

    evolve_shadow = client.post(
        "/v1/command-center/shadow/evolve", json={"reason": "risk_execution"}
    )
    assert evolve_shadow.status_code == 200
    shadow_payload = evolve_shadow.json()
    assert shadow_payload["ok"] is True
    assert shadow_payload["shadow"]["tier"] == "Shade"


def test_autonomy_loop_tick(client, monkeypatch, tmp_path):
    state_path = tmp_path / "command_center_state.json"
    monkeypatch.setattr(
        runtime_server, "_command_center_state_path", lambda: state_path
    )

    response = client.post(
        "/v1/command-center/loop/tick", json={"cycle_label": "hourly"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["loop"]["tick_count"] == 1
    assert payload["loop"]["last_cycle_label"] == "hourly"
