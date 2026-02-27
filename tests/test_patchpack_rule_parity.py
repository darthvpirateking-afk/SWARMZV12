from __future__ import annotations

import re
from pathlib import Path

from swarmz_runtime.verify import patchpacks


ROOT = Path(__file__).resolve().parents[1]


def _extract_js_array(js_text: str, const_name: str) -> list[str]:
    pattern = rf"const\s+{const_name}\s*=\s*\[(.*?)\];"
    match = re.search(pattern, js_text, re.DOTALL)
    if not match:
        raise AssertionError(f"missing JS constant: {const_name}")
    values = re.findall(r"\"([^\"]+)\"", match.group(1))
    return values


def _extract_js_string(js_text: str, const_name: str) -> str:
    pattern = rf"const\s+{const_name}\s*=\s*\"([^\"]+)\";"
    match = re.search(pattern, js_text)
    if not match:
        raise AssertionError(f"missing JS constant: {const_name}")
    return match.group(1)


def test_patchpack_python_js_rule_parity() -> None:
    js_text = (ROOT / "tools/validators/noCoreMutation.js").read_text(encoding="utf-8")
    js_forbidden = tuple(_extract_js_array(js_text, "FORBIDDEN_PREFIXES"))
    js_required = _extract_js_string(js_text, "REQUIRED_PREFIX")

    assert patchpacks.FORBIDDEN_PREFIXES == js_forbidden
    assert patchpacks.REQUIRED_PREFIX == js_required
