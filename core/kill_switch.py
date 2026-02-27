# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Kill Switch + Safe Halt layer to ensure safe shutdown.
"""

import os
import sys


def activate_kill_switch():
    """
    Activates the kill switch to halt all operations.
    """
    print("Kill switch activated. Halting all operations.")
    sys.exit(1)


def safe_halt():
    """
    Performs a safe halt by cleaning up resources.
    """
    print("Performing safe halt...")
    # Example: Clean up temporary files or close connections
    temp_files = ["temp1", "temp2"]  # Replace with actual temp files
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass
    print("Safe halt completed.")
