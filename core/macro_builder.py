# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Macro builder layer.

Converts frequent event sequences into simple macro records.
"""

from typing import Any, Dict, Iterable, List


def build_macros(sequences: Iterable[Dict[str, Any]], min_support: int = 2) -> List[Dict[str, Any]]:
	macros: List[Dict[str, Any]] = []
	for item in sequences:
		if not isinstance(item, dict):
			continue
		support = int(item.get("support", 0) or 0)
		if support >= min_support:
			macros.append({"name": item.get("name", "macro"), "support": support})
	return macros
