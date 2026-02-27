from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class DefaultCredential:
    product: str
    username: str
    password: str
    risk: str
    source: str = "default_creds_catalog"


DEFAULT_CREDS_DB: dict[str, list[DefaultCredential]] = {
    "tomcat": [
        DefaultCredential(
            product="tomcat", username="tomcat", password="tomcat", risk="high"
        )
    ],
    "jenkins": [
        DefaultCredential(
            product="jenkins", username="admin", password="admin", risk="high"
        )
    ],
    "routeros": [
        DefaultCredential(
            product="routeros", username="admin", password="admin", risk="critical"
        )
    ],
}


def get_default_creds_config(aggression: int, curiosity: int) -> dict[str, Any]:
    return {
        "enabled": aggression >= 20,
        "attempt_safe_subset": True,
        "max_attempts_per_service": 3 if aggression < 60 else 10,
        "enrich_with_banner_fingerprint": curiosity >= 50,
    }


def get_default_credentials(product: str) -> list[dict[str, str]]:
    records = DEFAULT_CREDS_DB.get((product or "").strip().lower(), [])
    return [asdict(item) for item in records]


def is_default_credential(
    username: str, password: str, product: str | None = None
) -> bool:
    product_key = (product or "").strip().lower()
    pools = (
        DEFAULT_CREDS_DB.values()
        if not product_key
        else [DEFAULT_CREDS_DB.get(product_key, [])]
    )
    for records in pools:
        for candidate in records:
            if candidate.username == username and candidate.password == password:
                return True
    return False
