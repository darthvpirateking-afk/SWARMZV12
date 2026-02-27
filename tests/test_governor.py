"""
Tests for the Governor module.
"""

import pytest
import time
import json
from pathlib import Path
from core.governor import Governor


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary config file for the Governor."""
    config = {
        "rate_limits": {
            "test_action": {"limit": 2, "period": 1},  # 2 actions per 1 second
            "default": {"limit": 5, "period": 60},
        },
        "concurrency_limit": 3,
    }
    config_file = tmp_path / "governor_config.json"
    config_file.write_text(json.dumps(config))
    return config_file


@pytest.fixture
def tmp_state(tmp_path: Path) -> Path:
    """Create a temporary state file path."""
    return tmp_path / "governor_state.json"


def test_governor_initialization_with_config(tmp_config: Path):
    """Test that the Governor loads configuration correctly."""
    governor = Governor(config_path=tmp_config)
    assert governor.concurrency_limit == 3
    assert governor.rate_limits["test_action"]["limit"] == 2


def test_rate_limiting_allows_actions_within_limit():
    """Test that actions are allowed when they are under the rate limit."""
    governor = Governor()  # Use default limits
    action = {"type": "some_action"}

    # Default is 10 per 60s, so 5 should be fine
    for _ in range(5):
        assert governor.admit_action(action) is True


def test_rate_limiting_denies_actions_exceeding_limit(tmp_config: Path):
    """Test that actions are denied once the rate limit is exceeded."""
    governor = Governor(config_path=tmp_config)
    action = {"type": "test_action"}  # Limit is 2 per 1s

    assert governor.admit_action(action) is True
    assert governor.admit_action(action) is True
    # The third action should be denied
    assert governor.admit_action(action) is False


def test_rate_limit_period_resets_correctly(tmp_config: Path):
    """Test that the rate limit counter resets after the period has passed."""
    governor = Governor(config_path=tmp_config)
    action = {"type": "test_action"}  # Limit is 2 per 1s

    assert governor.admit_action(action) is True
    assert governor.admit_action(action) is True
    assert governor.admit_action(action) is False

    # Wait for the period (1s) to pass
    time.sleep(1.1)

    # The limit should have reset
    assert governor.admit_action(action) is True


def test_concurrency_check_allows_below_limit():
    """Test that concurrency check passes when running missions are below the limit."""
    governor = Governor()
    governor.concurrency_limit = 5
    assert governor.check_concurrency(current_running=4) is True


def test_concurrency_check_denies_at_limit():
    """Test that concurrency check fails when running missions are at the limit."""
    governor = Governor()
    governor.concurrency_limit = 5
    assert governor.check_concurrency(current_running=5) is False


def test_default_rate_limit_is_applied(tmp_config: Path):
    """Test that the default rate limit is used for unspecified action types."""
    governor = Governor(config_path=tmp_config)
    action = {"type": "unspecified_action"}  # Should use default: 5 per 60s

    for i in range(5):
        assert governor.admit_action(action) is True, f"Failed on iteration {i+1}"

    assert governor.admit_action(action) is False


def test_state_is_saved_and_loaded(tmp_config: Path, tmp_state: Path):
    """Test that the governor's state is persisted and reloaded correctly."""
    # First, create a governor and perform an action to create state
    gov1 = Governor(config_path=tmp_config, state_path=tmp_state)
    action = {"type": "test_action"}
    gov1.admit_action(action)

    # The state file should now exist and contain one timestamp
    assert tmp_state.exists()
    state_content = json.loads(tmp_state.read_text())
    assert len(state_content["action_timestamps"]["test_action"]) == 1

    # Now, create a new governor instance from the same state file
    gov2 = Governor(config_path=tmp_config, state_path=tmp_state)

    # This new governor should already have the state of the first action
    assert len(gov2.action_timestamps["test_action"]) == 1

    # A second action should be admitted
    assert gov2.admit_action(action) is True

    # A third should be denied because the state was loaded
    assert gov2.admit_action(action) is False
