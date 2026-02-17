# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from core.activity_stream import record_event

def observed_write(path, data):
    """Write data to a file and log the operation."""
    try:
        with open(path, "wb") as f:
            f.write(data)
        record_event("system", "file_write", {"path": path, "size": len(data)})
    except Exception:
        record_event("system", "file_write", {"path": path, "size": 0, "error": True})
        raise

def observed_read(path):
    """Read data from a file and log the operation."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        record_event("system", "file_read", {"path": path})
        return data
    except Exception:
        record_event("system", "file_read", {"path": path, "error": True})
        raise
