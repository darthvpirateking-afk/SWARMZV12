import os
import shutil
import logging
import time
from pathlib import Path
from core.self_healing import verify_and_heal, compute_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrityStressTest")


def stress_test():
    target_file = Path("core/sovereign.py")
    backup_file = Path("data/kernel_backups/sovereign.py")

    if not target_file.exists():
        logger.error(f"{target_file} not found. Aborting.")
        return

    if not backup_file.exists():
        logger.info("Backup not found, creating baseline...")
        verify_and_heal()  # This creates backups if missing

    original_hash = compute_hash(target_file)
    logger.info(f"Original Hash: {original_hash}")

    # 1. Corrupt the file
    logger.warning("!!! CORRUPTING KERNEL FILE !!!")
    with open(target_file, "a") as f:
        f.write(
            "\n# CORRUPTION BY OTHER AGENT SIMULATION\nraise Exception('System Integrity Failure')\n"
        )

    corrupted_hash = compute_hash(target_file)
    logger.info(f"Corrupted Hash: {corrupted_hash}")
    assert original_hash != corrupted_hash

    # 2. Run Self-Healing
    logger.info("Running Self-Healing...")
    verify_and_heal()

    # 3. Verify Restoration
    restored_hash = compute_hash(target_file)
    logger.info(f"Restored Hash: {restored_hash}")

    if restored_hash == original_hash:
        logger.info("SUCCESS: Kernel file restored to gold-standard integrity.")
    else:
        logger.error("FAILURE: Kernel file restoration failed or hash mismatch.")
        exit(1)


if __name__ == "__main__":
    stress_test()
