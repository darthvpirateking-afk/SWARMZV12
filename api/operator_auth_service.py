import hmac
import os
from datetime import datetime, timezone
from pathlib import Path

from api.operator_auth_models import (
    OperatorAuthStatusResponse,
    OperatorAuthVerifyResponse,
)


class OperatorAuthService:
    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = Path(data_dir)

    def get_status(self) -> OperatorAuthStatusResponse:
        expected = self._expected_key()
        return OperatorAuthStatusResponse(
            ok=True,
            auth_mode="operator-key",
            key_configured=bool(expected),
            generated_at=datetime.now(timezone.utc),
        )

    def verify(self, operator_key: str) -> OperatorAuthVerifyResponse:
        expected = self._expected_key()
        if not expected:
            return OperatorAuthVerifyResponse(
                ok=False,
                authenticated=False,
                message="No operator key configured",
                generated_at=datetime.now(timezone.utc),
            )

        valid = hmac.compare_digest(operator_key.strip(), expected)
        return OperatorAuthVerifyResponse(
            ok=valid,
            authenticated=valid,
            message="authenticated" if valid else "invalid operator key",
            generated_at=datetime.now(timezone.utc),
        )

    def _expected_key(self) -> str:
        env_key = (
            os.getenv("OPERATOR_KEY") or os.getenv("SWARMZ_OPERATOR_PIN") or ""
        ).strip()
        if env_key:
            return env_key

        pin_file = self._data_dir / "operator_pin.txt"
        if pin_file.exists():
            try:
                return pin_file.read_text(encoding="utf-8").strip()
            except Exception:
                return ""
        return ""
