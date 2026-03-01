# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_scoring.py — Scoring Layer Tests

Validates multi-factor risk scoring and deterministic score calculation.
"""

from core.scoring import ScoringLayer, score, evaluate


def test_calculate_risk_low():
    """Low-risk action should score low."""
    layer = ScoringLayer()
    action = {
        "type": "read",
        "rank": "E",
        "reversibility": True,
        "dependencies": [],
    }

    risk = layer.calculate_risk(action)

    assert risk < 20  # read=5, E=0.5, reversible=0.7, no deps


def test_calculate_risk_high():
    """High-risk action should score high."""
    layer = ScoringLayer()
    action = {
        "type": "file_delete",
        "rank": "S",
        "reversibility": False,
        "dependencies": ["dep1", "dep2", "dep3"],
    }

    risk = layer.calculate_risk(action)

    assert risk > 80  # delete=90, S=5.0, non-reversible=1.0, deps


def test_calculate_risk_capped():
    """Risk should be capped at 100."""
    layer = ScoringLayer()
    action = {
        "type": "purchase",  # 95 base
        "rank": "S",  # 5.0x
        "reversibility": False,  # 1.0x
        "dependencies": ["d1", "d2", "d3", "d4", "d5"],  # 1.5x
    }

    risk = layer.calculate_risk(action)

    assert risk <= 100.0


def test_calculate_cost():
    """Should calculate resource cost."""
    layer = ScoringLayer()
    action = {
        "estimated_seconds": 60,
        "api_calls": 10,
        "storage_mb": 100,
    }

    cost = layer.calculate_cost(action)

    # base=1 + time=1.0 + api=1.0 + storage=1.0 = 4.0
    assert cost > 3.0


def test_calculate_complexity():
    """Should calculate 1-10 complexity."""
    layer = ScoringLayer()

    simple = {"steps": 1, "dependencies": [], "branches": 0}
    complex_action = {"steps": 5, "dependencies": ["d1", "d2", "d3"], "branches": 4}

    simple_score = layer.calculate_complexity(simple)
    complex_score = layer.calculate_complexity(complex_action)

    assert simple_score == 1
    assert complex_score > simple_score
    assert complex_score <= 10


def test_calculate_operator_confidence():
    """Should calculate operator confidence from history."""
    layer = ScoringLayer()
    action = {}

    novice_context = {
        "operator_success_rate": 0.3,
        "operator_rank": "E",
        "trials_completed": 0,
    }
    expert_context = {
        "operator_success_rate": 0.9,
        "operator_rank": "S",
        "trials_completed": 50,
    }

    novice_conf = layer.calculate_operator_confidence(action, novice_context)
    expert_conf = layer.calculate_operator_confidence(action, expert_context)

    assert novice_conf < expert_conf
    assert 0.0 <= novice_conf <= 1.0
    assert 0.0 <= expert_conf <= 1.0


def test_score_complete():
    """Should return ActionScore with all dimensions."""
    layer = ScoringLayer()
    action = {
        "type": "api_call",
        "rank": "B",
        "reversibility": True,
        "dependencies": ["dep1"],
        "estimated_seconds": 30,
        "api_calls": 5,
        "storage_mb": 10,
        "steps": 3,
        "branches": 1,
    }
    context = {
        "operator_success_rate": 0.7,
        "operator_rank": "B",
        "trials_completed": 20,
    }

    action_score = layer.score(action, context)

    assert action_score.risk > 0
    assert action_score.cost > 0
    assert action_score.reversibility is True
    assert action_score.complexity >= 1
    assert 0.0 <= action_score.operator_confidence <= 1.0
    assert len(action_score.reason) > 0


def test_evaluate_pass():
    """Low-risk action should pass evaluation."""
    action = {
        "type": "read",
        "rank": "E",
        "reversibility": True,
        "dependencies": [],
    }
    context = {}

    result = evaluate(action, context, risk_threshold=80.0)

    assert result.passed
    assert result.layer == "scoring"
    assert result.metadata["risk"] < 80.0


def test_evaluate_fail():
    """High-risk action should fail evaluation."""
    action = {
        "type": "purchase",
        "rank": "S",
        "reversibility": False,
        "dependencies": [],
    }
    context = {}

    result = evaluate(action, context, risk_threshold=50.0)

    assert not result.passed
    assert result.layer == "scoring"
    assert result.metadata["risk"] > 50.0


def test_evaluate_metadata():
    """Evaluation result should include score metadata."""
    action = {
        "type": "api_call",
        "rank": "C",
        "reversibility": True,
        "dependencies": [],
    }
    context = {}

    result = evaluate(action, context)

    assert "risk" in result.metadata
    assert "cost" in result.metadata
    assert "reversibility" in result.metadata
    assert "complexity" in result.metadata
    assert "operator_confidence" in result.metadata
    assert "threshold" in result.metadata
