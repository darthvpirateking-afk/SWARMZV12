import shutil
from pathlib import Path

qdir = Path("data/quarantine")
for f in qdir.glob("*.quarantined"):
    original_name = f.name.rsplit("_", 1)[0]
    if original_name != "rogue_virus.py":
        target = Path(original_name)
        if not target.exists():
            shutil.move(str(f), str(target))
            print(f"Restored {original_name}")
        else:
            print(f"Skipped {original_name} (already exists)")
