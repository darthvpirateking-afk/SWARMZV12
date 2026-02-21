# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/atomic.py â€” Atomic fileâ€‘write helpers for SWARMZ.

atomic_write_json:    write JSON to a temp file, then os.replace â†’ target.
atomic_append_jsonl:  append one JSON line with fileâ€‘level locking (bestâ€‘effort).

No external dependencies. Safe on Windows and POSIX.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Windows has no fcntl â€” locking disabled, but rename is still atomic
try:
    import fcntl as _fcntl
except ImportError:
    _fcntl = None


def atomic_write_json(path: Path, obj: Any, *, indent: int = 2) -> None:
    """Write *obj* as formatted JSON via tempâ€‘fileâ€‘thenâ€‘rename.

    On most fileâ€‘systems ``os.replace`` is atomic â€” readers will
    never see a truncated file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(obj, indent=indent, default=str), encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception:
        # clean up temp on failure
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def atomic_append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    """Append a single compact JSON line to *path*, bestâ€‘effort locked.

    Creates parent dirs and the file itself if missing.
    On Windows the write is still appendâ€‘mode (safe for singleâ€‘writer).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, separators=(",", ":"), default=str) + "\n"
    fd = open(path, "a", encoding="utf-8")
    try:
        if _fcntl is not None:
            _fcntl.flock(fd, _fcntl.LOCK_EX)
        fd.write(line)
        fd.flush()
    finally:
        if _fcntl is not None:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_UN)
            except Exception:
                pass
        fd.close()
