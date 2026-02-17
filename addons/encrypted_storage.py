# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Encrypted-at-rest storage for JSONL/event logs.

Uses HMAC-SHA256 authenticated XOR cipher when SWARMZ_ENCRYPTION_KEY is set.
Falls back to plaintext when no key is configured.

WARNING: The XOR+HMAC scheme here uses only Python stdlib and is NOT
a production-grade cipher.  For real deployments with sensitive data,
replace with the ``cryptography`` library's Fernet or AES-GCM.
This module is suitable for local-first / low-threat environments only.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# stdlib-only authenticated encryption using XOR + HMAC (simple, no ext deps)
# For production, replace with `cryptography` library's Fernet or AES-GCM.


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    import hmac as _hmac
    return _hmac.new(key, data, hashlib.sha256).digest()


def encrypt_blob(plaintext: bytes, passphrase: str) -> bytes:
    """Encrypt bytes with passphrase.  Returns nonceâ€–ciphertextâ€–mac."""
    key = _derive_key(passphrase)
    nonce = os.urandom(16)
    ct = _xor_bytes(plaintext, hashlib.sha256(key + nonce).digest())
    mac = _hmac_sha256(key, nonce + ct)
    return nonce + ct + mac


def decrypt_blob(blob: bytes, passphrase: str) -> bytes:
    """Decrypt blob.  Raises ValueError on bad key/tamper."""
    key = _derive_key(passphrase)
    if len(blob) < 48:
        raise ValueError("Blob too short")
    nonce = blob[:16]
    mac = blob[-32:]
    ct = blob[16:-32]
    expected = _hmac_sha256(key, nonce + ct)
    if not _constant_time_eq(mac, expected):
        raise ValueError("Authentication failed â€” wrong key or tampered data")
    return _xor_bytes(ct, hashlib.sha256(key + nonce).digest())


def _constant_time_eq(a: bytes, b: bytes) -> bool:
    import hmac as _hmac
    return _hmac.compare_digest(a, b)


# ---- JSONL helpers ---------------------------------------------------

def save_encrypted_jsonl(path: Path, records: List[Dict[str, Any]], passphrase: str) -> None:
    """Write list of dicts as encrypted JSONL blob."""
    text = "\n".join(json.dumps(r) for r in records)
    blob = encrypt_blob(text.encode(), passphrase)
    path.write_bytes(blob)


def load_encrypted_jsonl(path: Path, passphrase: str) -> List[Dict[str, Any]]:
    """Read encrypted JSONL blob â†’ list of dicts."""
    blob = path.read_bytes()
    text = decrypt_blob(blob, passphrase).decode()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def is_encryption_enabled() -> bool:
    """Check whether an encryption key is set."""
    from addons.config_ext import get_config
    cfg = get_config()
    return bool(cfg.get("encryption_key") or os.environ.get("SWARMZ_ENCRYPTION_KEY"))


def get_encryption_key() -> Optional[str]:
    from addons.config_ext import get_config
    cfg = get_config()
    return cfg.get("encryption_key") or os.environ.get("SWARMZ_ENCRYPTION_KEY") or None

