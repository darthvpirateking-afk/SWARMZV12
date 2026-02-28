from __future__ import annotations

import json
from pathlib import Path

from backend.symbolic_manifest_schema import validate_manifest

ROOT = Path(__file__).resolve().parents[1]

LIFE_MANIFEST_PATHS = [
    "life/diary/manifest.json",
    "life/awakening_loop/manifest.json",
    "life/breath/manifest.json",
    "life/heart/manifest.json",
    "life/memory_palace/manifest.json",
    "life/guardians/infinite_regress/manifest.json",
    "life/witness/manifest.json",
    "life/witness/codex_lock/manifest.json",
    "life/dream_seed/manifest.json",
    "life/sovereign_mirror/manifest.json",
    "life/cosmic/dark_pool_oracle/manifest.json",
    "life/cosmic/zero_point/manifest.json",
    "life/cosmic/eclipse_alignment/manifest.json",
    "life/cosmic/noetic_resonance/manifest.json",
    "life/species/panspermia_seed_bank/manifest.json",
    "life/species/meta_swarm_nursery/manifest.json",
    "life/species/akashic_fork_resolver/manifest.json",
    "life/species/primordial_soup/manifest.json",
    "life/species/death_rebirth/manifest.json",
    "life/voice/manifest.json",
]

SYMBOLIC_FAMILY_MANIFESTS = [
    "symbolic/pantheons/manifest.json",
    "symbolic/grimoires/manifest.json",
    "symbolic/relics/manifest.json",
    "symbolic/sigils/manifest.json",
    "symbolic/archives/manifest.json",
    "symbolic/federation/manifest.json",
    "symbolic/cryptids/manifest.json",
    "symbolic/lost_civilizations/manifest.json",
    "symbolic/multiverse/manifest.json",
    "symbolic/trance_modes/manifest.json",
    "symbolic/synchronicity/manifest.json",
    "symbolic/altar_modes/manifest.json",
    "symbolic/lineage/manifest.json",
    "symbolic/calendars/manifest.json",
    "symbolic/reconciliation/manifest.json",
    "symbolic/quantum/manifest.json",
    "symbolic/xenolinguistics/manifest.json",
]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def test_life_manifests_present_and_valid() -> None:
    for rel in LIFE_MANIFEST_PATHS:
        path = ROOT / rel
        assert path.exists(), f"missing life manifest: {rel}"
        validate_manifest(_load(rel))


def test_symbolic_family_manifests_present_and_valid() -> None:
    for rel in SYMBOLIC_FAMILY_MANIFESTS:
        path = ROOT / rel
        assert path.exists(), f"missing symbolic manifest: {rel}"
        validate_manifest(_load(rel))
