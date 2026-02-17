# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Hard Limits for Log Explosion layer to manage log size and retention.
"""

import os
import gzip
from datetime import datetime, timedelta

RETENTION_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10 MB
    "keep_days": 30,
}

def rotate_logs(log_file):
    """Rotate the log file if it exceeds the maximum size."""
    if os.path.getsize(log_file) > RETENTION_CONFIG["max_file_size"]:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        os.rename(log_file, f"{log_file}-{timestamp}.gz")
        with gzip.open(f"{log_file}-{timestamp}.gz", "wb") as f:
            with open(log_file, "rb") as original:
                f.write(original.read())
        open(log_file, "w").close()

def prune_logs(log_dir):
    """Prune logs older than the retention period."""
    cutoff_date = datetime.now() - timedelta(days=RETENTION_CONFIG["keep_days"])
    for file_name in os.listdir(log_dir):
        file_path = os.path.join(log_dir, file_name)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff_date:
                os.remove(file_path)
