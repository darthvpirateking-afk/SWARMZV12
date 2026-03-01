from __future__ import annotations

from pathlib import Path


def test_avatar_png_wired_in_frontend_components() -> None:
    dock = Path("frontend/src/components/CompanionAvatarDock.tsx").read_text(encoding="utf-8")
    identity = Path("frontend/src/components/OperatorIdentityPanel.tsx").read_text(encoding="utf-8")

    assert "/assets/my-avatar.png" in dock
    assert "/assets/my-avatar.png" in identity
    assert "AvatarMonarch" in dock
