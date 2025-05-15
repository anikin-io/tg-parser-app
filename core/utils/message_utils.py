import re
from telethon.tl.types import Message, MessageService, PeerUser


class MessageUtils:
    def is_system_message(self, message: Message) -> bool:
        """Проверяет, является ли сообщение системным"""
        # 1. Проверка типа сообщения
        if isinstance(message, MessageService):
            return True

        # 2. Проверка системных отправителей
        if message.from_id:
            system_ids = {
                777000,  # Telegram Notifications
                1087968824,  # GroupAnonymousBot
            }
            if isinstance(message.from_id, PeerUser):
                if message.from_id.user_id in system_ids:
                    return True

        # 3. Анализ текста сообщения
        if message.message:
            system_patterns = [
                r"(?i)(теперь (в группе|участник))",
                r"(?i)(joined (the|this) (group|channel))",
                r"(?i)(добавлен|присоединился)",
                r"(?i)(created (group|channel))",
            ]
            text = message.message.lower()
            if any(re.search(p, text) for p in system_patterns):
                return True

        # 4. Проверка пустого контента
        if not message.message and not message.media:
            return True

        return False
