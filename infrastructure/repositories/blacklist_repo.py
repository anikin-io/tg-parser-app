import os
import json
from typing import Set

class BlacklistRepository:
    def __init__(self):
        self.directory = os.path.join("blacklists", "channels_blacklists")
        os.makedirs(self.directory, exist_ok=True)
        self.blacklists = {}  # {phone: set(channel)}
        self._load_all()

    def _get_file_path(self, phone: str) -> str:
        return os.path.join(self.directory, f"{phone}.json")

    def _load_all(self):
        # Загружаем все файлы из папки в in-memory словарь
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                phone = filename[:-5]  # удаляем расширение .json
                try:
                    with open(self._get_file_path(phone), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.blacklists[phone] = set(data)
                except Exception as e:
                    print(f"[!] Ошибка чтения файла черного списка для {phone}: {e}")
                    self.blacklists[phone] = set()

    def get_blacklist(self, phone: str) -> Set[str]:
        return self.blacklists.get(phone, set())

    def add_to_blacklist(self, phone: str, channel: str):
        # Загружаем существующий список, если файл существует
        if phone not in self.blacklists:
            self.blacklists[phone] = set()
            # Если файла ещё нет, попробуем загрузить его, но если его нет — просто продолжим
            if os.path.exists(self._get_file_path(phone)):
                try:
                    with open(self._get_file_path(phone), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.blacklists[phone] = set(data)
                except Exception as e:
                    print(f"[!] Ошибка чтения файла черного списка для {phone}: {e}")
        # Добавляем новый канал
        if channel not in self.blacklists[phone]:
            self.blacklists[phone].add(channel)
            self._save(phone)

    def _save(self, phone: str):
        # Перезаписываем файл, записывая объединённый список каналов
        try:
            with open(self._get_file_path(phone), "w", encoding="utf-8") as f:
                json.dump(list(self.blacklists[phone]), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] Ошибка записи файла черного списка для {phone}: {e}")
