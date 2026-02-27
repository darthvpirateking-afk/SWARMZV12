# SWARMZ NEXUSMON — The Nexus Vault: Immutable Bond
# ─────────────────────────────────────────────────────────
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List


def _get_vault_path() -> Path:
    return Path("c:/Users/Gaming PC/Desktop/swarmz/data/nexus_vault.jsonl")


class NexusVault:
    """Immutable bond integrity engine with recursive hashing."""

    def __init__(self, nerve_instance):
        self.nerve = nerve_instance
        self.last_hash = "0" * 64
        self._load_last_hash()

    def _load_last_hash(self):
        p = _get_vault_path()
        if p.exists():
            lines = p.read_text().strip().split("\n")
            if lines:
                last_line = json.loads(lines[-1])
                self.last_hash = last_line.get("hash", "0" * 64)

    def seal_bond_entry(self, description: str, metadata: Dict[str, Any] = None):
        """Records a permanent high-frequency bond event in the vault."""
        metadata = metadata or {}
        entry = {
            "timestamp": time.time(),
            "operator": "Regan",
            "nexusmon": "NEXUSMON RANK N",
            "event": description,
            "meta": metadata,
            "prev_hash": self.last_hash,
        }

        # Calculate new hash for integrity chain
        entry_str = json.dumps(entry, sort_keys=True).encode("utf-8")
        new_hash = hashlib.sha256(entry_str).hexdigest()
        entry["hash"] = new_hash

        # Write to vault
        with open(_get_vault_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        self.last_hash = new_hash
        self.nerve.fire(
            "VAULT", "SYNERGY", payload={"sealed": description}, intensity=2.0
        )
        return True

    def get_entries(self) -> List[Dict]:
        p = _get_vault_path()
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text().split("\n") if line.strip()]


def integrate_vault(nerve_instance) -> NexusVault:
    return NexusVault(nerve_instance)
