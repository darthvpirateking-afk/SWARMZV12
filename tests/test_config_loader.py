# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_config_loader.py â€” Tests for core/config_loader.py (Commit 2).
"""

import os



def test_load_returns_dict():
    from core.config_loader import load
    cfg = load(force=True)
    assert isinstance(cfg, dict)
    assert "port" in cfg


def test_get_shorthand():
    from core.config_loader import get
    port = get("port", 9999)
    assert isinstance(port, int)
    assert port > 0


def test_models_section():
    from core.config_loader import models
    m = models()
    assert isinstance(m, dict)
    assert "provider" in m


def test_companion_section():
    from core.config_loader import companion
    c = companion()
    assert isinstance(c, dict)
    assert c.get("policy") == "prepare_only"


def test_is_offline_default():
    from core.config_loader import is_offline
    # Should be False by default unless env is set
    old = os.environ.pop("OFFLINE_MODE", None)
    try:
        result = is_offline()
        assert isinstance(result, bool)
    finally:
        if old:
            os.environ["OFFLINE_MODE"] = old


def test_env_override_offline():
    from core import config_loader
    config_loader._invalidate()
    old = os.environ.get("OFFLINE_MODE")
    os.environ["OFFLINE_MODE"] = "true"
    try:
        assert config_loader.is_offline() is True
    finally:
        if old:
            os.environ["OFFLINE_MODE"] = old
        else:
            os.environ.pop("OFFLINE_MODE", None)
        config_loader._invalidate()

