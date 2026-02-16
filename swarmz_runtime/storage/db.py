import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from swarmz_runtime.storage.schema import Mission, AuditEntry, Rune, MissionStatus


class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.missions_file = self.data_dir / "missions.jsonl"
        self.audit_file = self.data_dir / "audit.jsonl"
        self.runes_file = self.data_dir / "runes.json"
        self.state_file = self.data_dir / "system_state.json"
        
        self._init_files()
    
    def _init_files(self):
        if not self.missions_file.exists():
            self.missions_file.touch()
        if not self.audit_file.exists():
            self.audit_file.touch()
        if not self.runes_file.exists():
            self.runes_file.write_text(json.dumps({}))
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({"active_missions": 0, "pattern_counters": {}}))
    
    def save_mission(self, mission: Mission):
        # Atomic append, compact JSON
        with open(self.missions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(mission.model_dump(mode='json'), separators=(",", ":")) + "\n")
    
    def update_mission(self, mission_id: str, updates: Dict[str, Any]):
        missions = self.load_all_missions()
        for mission in missions:
            if mission["id"] == mission_id:
                mission.update(updates)
                mission["updated_at"] = datetime.now().isoformat()
        
        with open(self.missions_file, "w") as f:
            for mission in missions:
                f.write(json.dumps(mission) + "\n")
    
    def load_all_missions(self) -> List[Dict[str, Any]]:
        missions = []
        skipped_empty = 0
        bad_rows = []
        if self.missions_file.exists():
            with open(self.missions_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        skipped_empty += 1
                        continue
                    try:
                        missions.append(json.loads(line))
                    except Exception:
                        bad_rows.append(line.rstrip("\n"))
        if bad_rows:
            self._quarantine_bad_rows(bad_rows, source="missions.jsonl")
        self._last_missions_parse_stats = {
            "skipped_empty": skipped_empty,
            "bad_rows": len(bad_rows),
            "parsed": len(missions)
        }
        return missions
    
    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        missions = self.load_all_missions()
        for mission in missions:
            if mission["id"] == mission_id:
                return mission
        return None
    
    def get_active_missions(self) -> List[Dict[str, Any]]:
        missions = self.load_all_missions()
        return [m for m in missions if m["status"] == "active"]
    
    def log_audit(self, entry: AuditEntry):
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.model_dump(mode='json'), separators=(",", ":")) + "\n")
    
    def load_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        entries = []
        skipped_empty = 0
        bad_rows = []
        if self.audit_file.exists():
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        skipped_empty += 1
                        continue
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        bad_rows.append(line.rstrip("\n"))
        if bad_rows:
            self._quarantine_bad_rows(bad_rows, source="audit.jsonl")
        self._last_audit_parse_stats = {
            "skipped_empty": skipped_empty,
            "bad_rows": len(bad_rows),
            "parsed": len(entries)
        }
        return entries[-limit:]

    def _quarantine_bad_rows(self, bad_rows, source):
        quarantine_file = self.data_dir / "bad_rows.jsonl"
        with open(quarantine_file, "a", encoding="utf-8") as f:
            for row in bad_rows:
                f.write(json.dumps({"source": source, "raw": row}) + "\n")
        # Optionally: log to server log if available
        try:
            import logging
            logging.warning(f"Quarantined {len(bad_rows)} bad rows from {source}")
        except Exception:
            pass

    def get_last_parse_stats(self):
        return {
            "missions": getattr(self, "_last_missions_parse_stats", {}),
            "audit": getattr(self, "_last_audit_parse_stats", {})
        }
    
    def save_rune(self, rune: Rune):
        runes = self.load_runes()
        runes[rune.id] = rune.model_dump(mode='json')
        with open(self.runes_file, "w") as f:
            json.dump(runes, f, indent=2)
    
    def load_runes(self) -> Dict[str, Any]:
        if self.runes_file.exists():
            with open(self.runes_file, "r") as f:
                return json.load(f)
        return {}
    
    def get_rune(self, rune_id: str) -> Optional[Dict[str, Any]]:
        runes = self.load_runes()
        return runes.get(rune_id)
    
    def load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Recover from corrupted state file
                default = {"active_missions": 0, "pattern_counters": {}}
                self.save_state(default)
                return default
        return {"active_missions": 0, "pattern_counters": {}}
    
    def save_state(self, state: Dict[str, Any]):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def increment_pattern_counter(self, pattern: str) -> int:
        state = self.load_state()
        counters = state.get("pattern_counters", {})
        counters[pattern] = counters.get(pattern, 0) + 1
        state["pattern_counters"] = counters
        self.save_state(state)
        return counters[pattern]
    
    def get_pattern_counter(self, pattern: str) -> int:
        state = self.load_state()
        return state.get("pattern_counters", {}).get(pattern, 0)
