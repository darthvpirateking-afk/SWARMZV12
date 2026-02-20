"""Compatibility wrapper around runtime JSONL storage helpers."""

from typing import Any, Dict, Iterable, List, Tuple

from swarmz_runtime.storage.jsonl_utils import (
	append_jsonl as _storage_append,
	read_jsonl as _storage_read,
	write_jsonl as _storage_write,
)


def read_jsonl(path: str | Any) -> Tuple[List[Dict[str, Any]], int, int]:
	"""Return `(records, skipped, quarantined)` for legacy callers.

	Supports both runtime return shapes:
	- tuple: `(records, skipped, quarantined)`
	- list: `records`
	"""
	try:
		result = _storage_read(path)
	except Exception:
		return [], 0, 0

	if isinstance(result, tuple):
		records = result[0] if len(result) > 0 and isinstance(result[0], list) else []
		skipped = result[1] if len(result) > 1 and isinstance(result[1], int) else 0
		quarantined = result[2] if len(result) > 2 and isinstance(result[2], int) else 0
		return records, skipped, quarantined

	if isinstance(result, list):
		return result, 0, 0

	return [], 0, 0


def write_jsonl(path: str | Any, payload: Iterable[Dict[str, Any]] | Dict[str, Any]) -> None:
	"""Write JSONL data.

	- dict payload: append one record
	- iterable payload: overwrite with the full collection
	"""
	if isinstance(payload, dict):
		_storage_append(path, payload)
		return

	_storage_write(path, list(payload))


def append_jsonl(path: str | Any, record: Dict[str, Any]) -> None:
	_storage_append(path, record)


__all__ = ["read_jsonl", "write_jsonl", "append_jsonl"]
