# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tests for SWARMZ V3.0 feature patches:
  - Throne Layer
  - Realms
  - Swarm Tiers
  - Mission Ranks
  - Avatar Matrix
  - Operator Identity Layer API
  - Cockpit Live Data (cockpit/status)
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Patch 1 — Throne Layer (unit)
# ---------------------------------------------------------------------------


def test_throne_get_state():
    from swarmz_runtime.core.throne import ThroneLayer

    throne = ThroneLayer()
    state = throne.get_state()
    assert state["identity"] == "SOVEREIGN_OPERATOR"
    assert state["status"] == "SOVEREIGN"
    assert state["active_decrees"] == 0
    assert state["total_decrees"] == 0
    assert isinstance(state["constitution"], list)
    assert len(state["constitution"]) >= 5


def test_throne_issue_decree():
    from swarmz_runtime.core.throne import ThroneLayer

    throne = ThroneLayer()
    decree = throne.issue_decree("Test Decree", "This is a test body")
    assert decree.decree_id.startswith("DECREE-")
    assert decree.title == "Test Decree"
    assert decree.body == "This is a test body"
    assert decree.authority_level == "SOVEREIGN"
    assert decree.active is True

    state = throne.get_state()
    assert state["total_decrees"] == 1
    assert state["active_decrees"] == 1


def test_throne_ledger():
    from swarmz_runtime.core.throne import ThroneLayer

    throne = ThroneLayer()
    throne.issue_decree("Decree A", "Body A")
    throne.issue_decree("Decree B", "Body B", authority_level="OPERATOR")
    ledger = throne.get_ledger()
    assert len(ledger) == 2
    assert ledger[0]["title"] == "Decree A"
    assert ledger[1]["authority_level"] == "OPERATOR"


def test_throne_singleton():
    from swarmz_runtime.core.throne import get_throne

    t1 = get_throne()
    t2 = get_throne()
    assert t1 is t2


# ---------------------------------------------------------------------------
# Patch 2 — Realms (unit)
# ---------------------------------------------------------------------------


def test_realms_built_in():
    from swarmz_runtime.core.realms import RealmRegistry

    registry = RealmRegistry()
    realms = registry.list_realms()
    names = [r["name"] for r in realms]
    assert "COMBAT" in names
    assert "INTEL" in names
    assert "SCIENCE" in names
    assert "ENTERPRISE" in names
    assert "CYBER" in names
    assert "CLOUD" in names
    assert "ROBOTICS" in names
    assert "LEARNING" in names
    assert len(realms) == 8


def test_realms_get_by_id():
    from swarmz_runtime.core.realms import RealmRegistry

    registry = RealmRegistry()
    realm = registry.get_realm("combat")
    assert realm is not None
    assert realm["realm_id"] == "combat"
    assert realm["name"] == "COMBAT"


def test_realms_get_missing():
    from swarmz_runtime.core.realms import RealmRegistry

    registry = RealmRegistry()
    assert registry.get_realm("nonexistent") is None


def test_realms_create_custom():
    from swarmz_runtime.core.realms import RealmRegistry

    registry = RealmRegistry()
    realm = registry.create_realm("CUSTOM", "A custom realm for testing")
    assert realm["realm_id"].startswith("realm-")
    assert realm["name"] == "CUSTOM"
    assert realm["description"] == "A custom realm for testing"
    assert realm["active"] is True


def test_realms_singleton():
    from swarmz_runtime.core.realms import get_realm_registry

    r1 = get_realm_registry()
    r2 = get_realm_registry()
    assert r1 is r2


# ---------------------------------------------------------------------------
# Patch 3 — Swarm Tiers (unit)
# ---------------------------------------------------------------------------


def test_swarm_tiers_list():
    from swarmz_runtime.core.swarm_tiers import list_tiers

    tiers = list_tiers()
    assert len(tiers) == 6
    ids = [t["id"] for t in tiers]
    assert "RECRUIT" in ids
    assert "SCOUT" in ids
    assert "OPERATIVE" in ids
    assert "GUARDIAN" in ids
    assert "COMMANDER" in ids
    assert "SOVEREIGN" in ids


def test_swarm_tiers_get_by_id():
    from swarmz_runtime.core.swarm_tiers import get_tier

    tier = get_tier("OPERATIVE")
    assert tier is not None
    assert tier["tier"] == 2
    assert "execute" in tier["capabilities"]


def test_swarm_tiers_get_missing():
    from swarmz_runtime.core.swarm_tiers import get_tier

    assert get_tier("NONEXISTENT") is None


def test_swarm_tiers_resolve_by_missions():
    from swarmz_runtime.core.swarm_tiers import resolve_tier_for_missions

    assert resolve_tier_for_missions(0)["id"] == "RECRUIT"
    assert resolve_tier_for_missions(4)["id"] == "RECRUIT"
    assert resolve_tier_for_missions(5)["id"] == "SCOUT"
    assert resolve_tier_for_missions(25)["id"] == "OPERATIVE"
    assert resolve_tier_for_missions(75)["id"] == "GUARDIAN"
    assert resolve_tier_for_missions(200)["id"] == "COMMANDER"
    assert resolve_tier_for_missions(500)["id"] == "SOVEREIGN"
    assert resolve_tier_for_missions(9999)["id"] == "SOVEREIGN"


# ---------------------------------------------------------------------------
# Patch 4 — Mission Ranks (unit)
# ---------------------------------------------------------------------------


def test_mission_ranks_list():
    from swarmz_runtime.core.mission_ranks import list_ranks

    ranks = list_ranks()
    assert len(ranks) == 5
    ids = [r["rank"] for r in ranks]
    assert "DELTA" in ids
    assert "CHARLIE" in ids
    assert "BRAVO" in ids
    assert "ALPHA" in ids
    assert "THRONE" in ids


def test_mission_ranks_get_by_id():
    from swarmz_runtime.core.mission_ranks import get_rank

    rank = get_rank("ALPHA")
    assert rank is not None
    assert rank["level"] == 4
    assert rank["color"] == "#dc3545"


def test_mission_ranks_get_missing():
    from swarmz_runtime.core.mission_ranks import get_rank

    assert get_rank("UNKNOWN") is None


def test_mission_ranks_classify():
    from swarmz_runtime.core.mission_ranks import classify_mission

    assert classify_mission(0.0)["rank"] == "DELTA"
    assert classify_mission(0.1)["rank"] == "DELTA"
    assert classify_mission(0.3)["rank"] == "CHARLIE"
    assert classify_mission(0.5)["rank"] == "BRAVO"
    assert classify_mission(0.7)["rank"] == "ALPHA"
    assert classify_mission(0.9)["rank"] == "THRONE"
    assert classify_mission(1.0)["rank"] == "THRONE"


# ---------------------------------------------------------------------------
# Patch 5 — Avatar Matrix (unit)
# ---------------------------------------------------------------------------


def test_avatar_matrix_state():
    from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix

    matrix = AvatarMatrix("TEST_OPERATOR")
    state = matrix.get_matrix_state()
    assert state["operator_rank"] == "TEST_OPERATOR"
    assert state["active_variant"] == "omega"
    assert state["current_state"] == "neutral"
    assert "omega" in state["available_variants"]
    assert "infinity" in state["available_variants"]
    assert "omega_plus" in state["available_variants"]


def test_avatar_matrix_set_valid_state():
    from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix

    matrix = AvatarMatrix()
    result = matrix.set_state("focused")
    assert result["ok"] is True
    assert result["state"] == "focused"
    assert matrix._current_state == "focused"


def test_avatar_matrix_set_invalid_state():
    from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix

    matrix = AvatarMatrix()
    result = matrix.set_state("flying")
    assert result["ok"] is False
    assert "Invalid state" in result["error"]


def test_avatar_matrix_switch_variant():
    from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix

    matrix = AvatarMatrix()
    result = matrix.switch_variant("infinity")
    assert result["ok"] is True
    assert matrix._active_variant == "infinity"


def test_avatar_matrix_switch_invalid_variant():
    from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix

    matrix = AvatarMatrix()
    result = matrix.switch_variant("unknown_variant")
    assert result["ok"] is False


def test_avatar_matrix_singleton():
    from swarmz_runtime.avatar.avatar_matrix import get_avatar_matrix

    m1 = get_avatar_matrix()
    m2 = get_avatar_matrix()
    assert m1 is m2


# ---------------------------------------------------------------------------
# Patch 6 — Operator Identity Layer API (integration via TestClient)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    from swarmz_server import app

    return TestClient(app)


def test_operator_identity_endpoint(client):
    r = client.get("/v1/operator/identity")
    assert r.status_code == 200
    data = r.json()
    assert data["identity"] == "SOVEREIGN_OPERATOR"
    assert "prime_directive" in data
    assert isinstance(data["charter_sections"], list)


def test_operator_charter_endpoint(client):
    r = client.get("/v1/operator/charter")
    assert r.status_code == 200
    data = r.json()
    assert "prime_directive" in data
    assert "sections" in data
    assert "system_primitives" in data
    assert "operating_matrix" in data


def test_operator_sovereignty_endpoint(client):
    r = client.get("/v1/operator/sovereignty")
    assert r.status_code == 200
    data = r.json()
    assert data["sovereignty"] == "full"
    assert data["status"] == "SOVEREIGN"
    assert "change_vector" in data


# ---------------------------------------------------------------------------
# Patches 1–5 via HTTP (Throne, Realms, Tiers, Ranks, Avatar Matrix)
# ---------------------------------------------------------------------------


def test_throne_state_endpoint(client):
    r = client.get("/v1/throne/state")
    assert r.status_code == 200
    data = r.json()
    assert data["identity"] == "SOVEREIGN_OPERATOR"
    assert data["status"] == "SOVEREIGN"


def test_throne_ledger_endpoint(client):
    r = client.get("/v1/throne/ledger")
    assert r.status_code == 200
    assert "ledger" in r.json()


def test_throne_decree_endpoint(client):
    r = client.post(
        "/v1/throne/decree",
        json={"title": "CI Test Decree", "body": "Issued during automated tests"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["decree_id"].startswith("DECREE-")


def test_realms_list_endpoint(client):
    r = client.get("/v1/realms")
    assert r.status_code == 200
    data = r.json()
    assert "realms" in data
    assert len(data["realms"]) >= 8


def test_realms_get_endpoint(client):
    r = client.get("/v1/realms/combat")
    assert r.status_code == 200
    data = r.json()
    assert data["realm_id"] == "combat"


def test_realms_get_404(client):
    r = client.get("/v1/realms/doesnotexist")
    assert r.status_code == 404


def test_realms_create_endpoint(client):
    r = client.post(
        "/v1/realms",
        json={"name": "TESTZONE", "description": "Test realm created in CI"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["realm"]["name"] == "TESTZONE"


def test_swarm_tiers_endpoint(client):
    r = client.get("/v1/swarm/tiers")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tiers"]) == 6


def test_swarm_tier_detail_endpoint(client):
    r = client.get("/v1/swarm/tiers/COMMANDER")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == 4


def test_swarm_tier_404(client):
    r = client.get("/v1/swarm/tiers/UNKNOWNTIER")
    assert r.status_code == 404


def test_mission_ranks_endpoint(client):
    r = client.get("/v1/missions/ranks")
    assert r.status_code == 200
    data = r.json()
    assert len(data["ranks"]) == 5


def test_mission_rank_detail_endpoint(client):
    r = client.get("/v1/missions/ranks/THRONE")
    assert r.status_code == 200
    data = r.json()
    assert data["level"] == 5


def test_mission_rank_404(client):
    r = client.get("/v1/missions/ranks/UNKNOWN")
    assert r.status_code == 404


def test_avatar_matrix_endpoint(client):
    r = client.get("/v1/avatar/matrix")
    assert r.status_code == 200
    data = r.json()
    assert "active_variant" in data
    assert "current_state" in data
    assert "available_variants" in data


def test_avatar_matrix_set_state_endpoint(client):
    r = client.post("/v1/avatar/matrix/state", json={"state": "focused"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["state"] == "focused"


def test_avatar_matrix_set_invalid_state_endpoint(client):
    r = client.post("/v1/avatar/matrix/state", json={"state": "flying"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False


# ---------------------------------------------------------------------------
# Patch 7 — Cockpit Live Data
# ---------------------------------------------------------------------------


def test_cockpit_status_endpoint(client):
    r = client.get("/cockpit/status")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "throne" in data
    assert "avatar" in data
    assert "realms" in data
    assert "swarm_tiers" in data
    assert "mission_ranks" in data
    assert "panels" in data
    assert "evolution" in data
    assert "monarch_mode" in data
    assert "active_summons" in data
    assert "abilities" in data
    assert "chip_state" in data
    assert isinstance(data["panels"], list)
    assert data["realms"]["total"] >= 8
