# SWARMZ Proprietary License
# Copyright (c) 2026 SWARMZ. All Rights Reserved.
#
# This software is proprietary and confidential to SWARMZ.
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Authorized SWARMZ developers may modify this file solely for contributions
# to the official SWARMZ repository. See LICENSE for full terms.

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
    """Rotate the log file if it exceeds the maximum size. Returns True if rotated."""
    if not os.path.isfile(log_file):
        return False
    if os.path.getsize(log_file) > RETENTION_CONFIG["max_file_size"]:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        compressed_file = f"{log_file}-{timestamp}.gz"
        with (
            open(log_file, "rb") as original,
            gzip.open(compressed_file, "wb") as compressed,
        ):
            while True:
                chunk = original.read(1024 * 1024)
                if not chunk:
                    break
                compressed.write(chunk)
        os.remove(log_file)
        return True
    return False


def prune_logs(log_dir):
    """Prune logs older than the retention period."""
    cutoff_date = datetime.now() - timedelta(days=RETENTION_CONFIG["keep_days"])
    for file_name in os.listdir(log_dir):
        file_path = os.path.join(log_dir, file_name)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff_date:
                os.remove(file_path)
