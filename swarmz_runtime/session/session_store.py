import json
import os


class SessionStore:
    def __init__(self, storage_path="session_logs.json"):
        self.storage_path = storage_path
        self.sessions = []
        self._load_sessions()

    def _load_sessions(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as file:
                self.sessions = json.load(file)

    def append_session(self, session_data: dict):
        self.sessions.append(session_data)
        self._save_sessions()

    def _save_sessions(self):
        with open(self.storage_path, "w") as file:
            json.dump(self.sessions, file, indent=4)

    def get_sessions(self):
        return self.sessions
