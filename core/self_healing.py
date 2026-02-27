import shutil
import logging
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

# Essential Kernel Files that must never be broken
KERNEL_FILES = [
    "core/sovereign.py",
    "core/reversible.py",
    "core/telemetry.py",
    "core/capability_flags.py",
    "core/policy_eval.py",
]

BACKUP_DIR = Path("data/kernel_backups")


def compute_hash(path: Path) -> str:
    """Compute SHA256 of a file."""
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def backup_kernel():
    """Create a gold-standard backup of the current kernel."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in KERNEL_FILES:
        src = Path(file_path)
        if src.exists():
            dst = BACKUP_DIR / src.name
            shutil.copy2(src, dst)
            logger.info(f"Kerneled Backup created: {file_path}")


def verify_and_heal():
    """Check kernel integrity and restore if hashes don't match or files missing."""
    if not BACKUP_DIR.exists():
        backup_kernel()
        return

    healed_files = []
    for file_path in KERNEL_FILES:
        target = Path(file_path)
        backup = BACKUP_DIR / target.name

        if not target.exists() or compute_hash(target) != compute_hash(backup):
            if backup.exists():
                shutil.copy2(backup, target)
                healed_files.append(file_path)

    if healed_files:
        logger.warning(f"Self-Healing Triggered! Restored: {', '.join(healed_files)}")
        from core.telemetry import telemetry

        telemetry.log_action(
            "CRITICAL", "SelfHealing", f"Restored integrity for: {healed_files}"
        )
    else:
        logger.info("Kernel integrity verified. All systems nominal.")


if __name__ == "__main__":
    verify_and_heal()
