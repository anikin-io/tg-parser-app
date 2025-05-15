import re
from typing import Optional
from urllib.parse import urlparse

import requests

from config import config


class TelegramUrlsUtils:

    @staticmethod
    def parse_chat_link(url: str) -> tuple[str, Optional[int]]:
        """
        Если URL содержит дополнительную часть (например, /1), то возвращает базовый URL и topic_id.
        Иначе возвращает исходный URL и None.
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[-1].isdigit():
            topic_id = int(path_parts[-1])
            base_url = f"https://t.me/{path_parts[0]}"
            return base_url, topic_id
        return url, None

    @staticmethod
    def validate_telegram_url(url: str) -> bool:
        """Проверяет валидность URL телеграм канала/чата"""
        url = url.strip().lower()

        # Обработка @username формата
        if url.startswith("@"):
            url = f"https://t.me/{url[1:]}"

        # Основная проверка через парсинг URL
        try:
            result = urlparse(url)
            if result.scheme not in ("http", "https", ""):
                return False

            # Проверяем домен и путь
            if result.netloc not in ("t.me", "telegram.me"):
                return False

            if not result.path.strip("/"):
                return False  # Путь не может быть пустым

            # Разрешаем форматы:
            # t.me/username
            # t.me/username/123 (для топиков)
            path_parts = result.path.split("/")
            if len(path_parts) < 2:
                return False

            # Проверяем валидность username
            username = path_parts[1]
            if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
                return False

            return True

        except:
            return False

    @staticmethod
    def extract_channel_info_from_url(url: str) -> Optional[tuple]:
        """
        Извлекает информацию о канале из различных форматов URL

        Возвращает кортеж:
        (тип_идентификатора, значение) или None

        Типы:
        'username' - короткое имя канала
        'public_id' - публичный ID формата 123456789
        'private_id' - приватный ID формата 1234567890
        """
        # Удаляем схему и параметры
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        # Обрабатываем разные форматы URL
        patterns = [
            # Формат t.me/c/1234567890/54321
            (r"^c/(?P<channel_id>-?\d+)(/|$)", "public_id"),
            # Формат t.me/joinchat/ABCDEF12345
            (r"^joinchat/(?P<private_id>\w+)$", "private_id"),
            # Стандартный username
            (r"^(?P<username>[a-zA-Z0-9_]{5,32})(/|$)", "username"),
        ]

        for pattern, id_type in patterns:
            match = re.search(pattern, path)
            if match:
                return (id_type, match.group(1))

        return None

    @classmethod
    def get_channel_id_by_username(cls, username: str) -> Optional[int]:
        """
        Получает ID Telegram канала/чата по username через Bot API

        :param bot_token: Токен Telegram бота
        :param username: Имя канала (с @ или без)
        :return: ID канала или None при ошибке
        """
        bot_token = config.API_TOKEN
        # Удаляем @ в начале, если есть
        username = username.lstrip("@")

        url = f"https://api.telegram.org/bot{bot_token}/getChat"
        params = {"chat_id": f"@{username}"}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("ok") and data.get("result"):
                return data["result"]["id"]

            print(f"[!] Ошибка: {data.get('description')}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"[!] Ошибка подключения: {str(e)}")
            return None
        except Exception as e:
            print(f"[!] Необработанная ошибка: {str(e)}")
            return None

    @classmethod
    def get_channel_id_by_url(cls, url: str) -> Optional[int]:
        """
        Получает ID канала по URL используя подходящий метод
        """
        channel_info = cls.extract_channel_info_from_url(url)

        if not channel_info:
            print("[!] Не удалось распознать URL канала")
            return None

        id_type, value = channel_info

        # Обработка разных типов идентификаторов
        if id_type == "username":

            return cls.get_channel_id_by_username(value)

        elif id_type == "public_id":
            try:
                return int(value)
            except ValueError:
                print("[!] Некорректный ID в URL")
                return None

        elif id_type == "private_id":
            print("[!] Приватные каналы по invite-ссылкам не поддерживаются")
            return None

        return None
    
    @classmethod
    def get_channel_username_by_url(cls, url: str) -> Optional[str]:
        """
        Извлекает юзернейм из URL канала.
        Возвращает None для некорректных URL или не username-форматов.
        """
        # Предварительная обработка URL с @
        if url.startswith("@"):
            url = f"https://t.me/{url[1:]}"

        # Используем существующий метод парсинга
        result = cls.extract_channel_info_from_url(url)
        
        if result and result[0] == "username":
            return result[1]
        return None
