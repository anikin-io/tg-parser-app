import json
import os

BASE_DIR = os.getcwd()
SESSIONS_DIR = os.path.join(BASE_DIR, "res_sessions")


class SessionRepository:
    @staticmethod
    def session_exists(phone):
        path = os.path.join(SESSIONS_DIR, f"{phone}.session")
        if os.path.exists(path):
            return path
        else:
            return None

    @staticmethod
    def get_api_data(phone):
        config_path = os.path.join(SESSIONS_DIR, f"{phone}.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
