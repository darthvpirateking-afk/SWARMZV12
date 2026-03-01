from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_observatory_directories_exist_and_are_writable() -> None:
    for name in ("diary", "witness", "traces", "memory_palace"):
        directory = ROOT / "observatory" / name
        assert directory.exists(), str(directory)
        assert directory.is_dir(), str(directory)

        probe = directory / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        assert probe.exists(), str(probe)
        probe.unlink()
