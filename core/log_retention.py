# MIT License
# Copyright (c) 2026 SWARMZ
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
