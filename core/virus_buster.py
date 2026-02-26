import os
import shutil
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

logger = logging.getLogger("VirusBuster")

# --- WHITELIST OF LEGITIMATE ROOT SCRIPTS ---
WHITELISTED_ROOT_SCRIPTS = {
    "APP_STORE_BUILD.cmd", "CREATE_SWARMZ_APP_ICON.ps1", "FIX_SWARMZ_LAUNCHERS.py",
    "HEALTHCHECK.py", "ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py", "PACK_EXE.ps1",
    "PHONE_MODE.cmd", "PHONE_MODE.ps1", "RUN.cmd", "RUN.ps1", "RUN.sh",
    "SWARMZ_DAEMON_UP.cmd", "SWARMZ_DAEMON_UP.ps1", "SWARMZ_DOCTOR.cmd",
    "SWARMZ_DOCTOR.ps1", "SWARMZ_HOLOGRAM_SERVICE.ps1", "SWARMZ_MANUAL.cmd",
    "SWARMZ_MANUAL.ps1", "SWARMZ_ONE_BUTTON_DEPLOY.ps1", "SWARMZ_ONE_BUTTON_START.cmd",
    "SWARMZ_ONE_BUTTON_START.ps1", "SWARMZ_PROFILE.cmd", "SWARMZ_PROFILE.ps1",
    "SWARMZ_SMOKE_TEST.cmd", "SWARMZ_SMOKE_TEST.ps1", "SWARMZ_SMOKE.cmd",
    "SWARMZ_SMOKE.ps1", "SWARMZ_UP.cmd", "SWARMZ_UP.ps1", "SWARMZ_V5_LIVE_SETUP.ps1",
    "SWARMZ_V5_WSL_LIBVIRT_BOOTSTRAP.ps1", "SWARMZ_WSL_HOST_RECOVERY.ps1",
    "termux_hologram_run.sh", "termux_hologram_setup.sh", "termux_run.sh", "termux_setup.sh",
    "companion_cli.py", "companion_examples.py", "companion.py", "evaluation.py",
    "event_hooks.py", "examples.py", "run_server.py", "run_swarmz.py", "run.py",
    "self_check.py", "server_legacy_overlay.py", "setup_theorem_kb.py", "showcase.py",
    "swarm_runner.py", "swarmz_cli.py", "swarmz_server.py", "swarmz.py", "test_arena.py",
    "test_companion.py", "test_console_endpoints.py", "test_ecosystem.py", "test_galileo.py",
    "test_integration.py", "test_kernel_ignition.py", "test_mission_jsonl_robust.py",
    "nexusmon_operator_rank.py", "nexusmon_organism.py", "nexusmon_performance.py",
    "nexusmon_plugins.py", "nexusmon_signal_modules.py", "nexusmon_cognition.py",
    "nexusmon_mission_engine.py", "nexusmon_artifact_vault.py", "nexusmon_mentality.py",
    "nexusmon_sensorium.py", "nexusmon_forge.py", "nexusmon_nexus_vault.py",
    "nexusmon_linguistics.py", "sovereign_activation.py", "regan_message.py",
    "infuse_language_culture.py", "test_verification_runner.py", "test_operator_rank.py",
    "test_runtime_infra.py", "test_security_module.py", "test_swarmz_server.py",
    "test_swarmz.py", "test_ui.py",
    "timeline_store.py", "TOOLS_REPO_MAP.py", "_call_ollama.py", "jsonl_utils.py",
    "example_requests.sh", "install_and_run.sh", "examples.py", "run_server.py", "run_swarmz.py"
}

QUARANTINE_DIR = Path("data/quarantine")
MALICIOUS_EXTENSIONS = {".vbs", ".vbe", ".hta", ".js", ".php", ".exe"} 

class VirusBuster:
    """
    Active Defense System for SWARMZ.
    "Fights viruses like MegaMan."
    """
    
    def __init__(self):
        self.stats_path = Path("data/buster_stats.json")
        self.plasma_energy = 100
        self.viruses_neutralized = 0
        self.last_scan_result = []
        self._load_stats()

    def _load_stats(self):
        if self.stats_path.exists():
            try:
                data = json.loads(self.stats_path.read_text())
                self.viruses_neutralized = data.get("viruses_neutralized", 0)
                # Energy doesn't persist, starts full each session for now
            except:
                pass

    def _save_stats(self):
        self.stats_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "viruses_neutralized": self.viruses_neutralized,
            "last_updated": datetime.now().isoformat()
        }
        self.stats_path.write_text(json.dumps(data, indent=2))

    def scan_root(self) -> List[Path]:
        """Scan root for rogue files (Charge Buster)."""
        root = Path(".")
        rogues = []
        for file in root.iterdir():
            if not file.is_file():
                continue
            
            name = file.name
            ext = file.suffix.lower()

            # 1. Whitelist check (exact or prefix)
            if name in WHITELISTED_ROOT_SCRIPTS or name.startswith("nexusmon_") or name.startswith("test_") or name.startswith("_"):
                continue

            # 2. Unknown scripts in root
            if (ext in [".py", ".sh", ".ps1", ".cmd", ".bat"]):
                if name.startswith(".") or name in ["config.json", "package.json", "run.py", "swarmz.py"]:
                    continue
                rogues.append(file)
            
            # 2. Dangerous extensions
            elif ext in MALICIOUS_EXTENSIONS:
                # Except known ones like SWARMZ.spec or package-lock.json (if we had it)
                if name == "package.json": continue 
                rogues.append(file)
                
        return rogues

    def neutralize(self, file_path: Path):
        """Neutralize a virus (Buster Shot)."""
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        dst = QUARANTINE_DIR / f"{file_path.name}_{int(datetime.now().timestamp())}.quarantined"
        
        try:
            logger.warning(f"X-BUSTER FIRE: Neutralizing rogue file {file_path}")
            shutil.move(str(file_path), str(dst))
            self.viruses_neutralized += 1
            self.plasma_energy = max(0, self.plasma_energy - 10)
            self._save_stats()
            from core.telemetry import telemetry
            telemetry.log_action("WARNING", "BusterDefense", f"X-BUSTER: ROGUE {file_path.name} NEUTRALIZED")
        except Exception as e:
            logger.error(f"X-BUSTER JAMMED: Could not neutralize {file_path}: {e}")

    def defend_system(self):
        """Main defense loop (Powered by X-Buster)."""
        rogues = self.scan_root()
        if rogues:
            logger.info(f"SCAN COMPLETE: {len(rogues)} virally-active entities detected.")
            for rogue in rogues:
                self.neutralize(rogue)
        else:
            logger.info("SYSTEM NOMINAL: No viral signatures found in the Substrate.")

    def get_status(self) -> Dict[str, Any]:
        """Status for the Cockpit UI."""
        return {
            "plasma_energy": self.plasma_energy,
            "viruses_defeated": self.viruses_neutralized,
            "status": "READY" if self.plasma_energy > 0 else "RECHARGING"
        }

# Global Instance
buster = VirusBuster()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    buster.defend_system()
