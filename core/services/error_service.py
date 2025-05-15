import asyncio

from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    ChannelsTooMuchError,
    FloodWaitError,
    PeerFloodError,
)

from config.statuses import STATUS_SPAM_BLOCK
from core.domain.exceptions import CustomPeerFloodError


class ErrorHandlerService:
    def __init__(self, account_repo):
        self.account_repo = account_repo

    async def _handle_group_fetch_error(self, error: Exception, phone: str):
        """Обработчик ошибок при получении списка групп"""
        if isinstance(error, FloodWaitError):
            print(f"[!] Лимит запросов. Жду {error.seconds} сек. | {phone}")
            await asyncio.sleep(error.seconds)
        elif isinstance(error, PeerFloodError):
            print(f"[!] Получил спамблок от Telegram | {phone}")
            self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            raise CustomPeerFloodError(phone, error) from error
        else:
            print(f"[!] Неизвестная ошибка: {str(error)} | {phone}")

    async def _handle_forward_error(self, error, phone, channel):
        """Обработка ошибок пересылки"""
        if isinstance(error, FloodWaitError):
            print(f"[!] Лимит запросов. Жду {error.seconds} сек | {phone}")
            await asyncio.sleep(error.seconds)
        elif isinstance(error, PeerFloodError):
            print(f"[!] Получил спамблок от Telegram | {phone}")
            self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            raise CustomPeerFloodError(phone, error) from error
        elif "spam" in str(error).lower():
            print(f"[!] Получил спамблок от Telegram | {phone}")
            self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            raise CustomPeerFloodError(phone, error) from error
        elif "Cannot send requests while disconnected" in str(error):
            print(f"[!] Выкинуло из аккаунта, возможно получил бан | {phone}")
            self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            raise CustomPeerFloodError(phone, error) from error
        else:
            print(f"[!] Ошибка при пересылке в {channel.title}: {error} | {phone}")

    async def _handle_join_errors(self, error, phone, chat_url):
        """Обработка ошибок вступления"""
        if isinstance(error, ChannelPrivateError):
            print(
                f"[!] Чат/канал {chat_url} приватный или аккаунт в нем забанен | {phone}"
            )
        elif isinstance(error, ChannelInvalidError):
            print(f"[!] Неверный объект чата/канала {chat_url} | {phone}")
        elif isinstance(error, ChannelsTooMuchError):
            print(
                f"[!] Аккаунт присоединился к слишком большому числу супергрупп/каналов {chat_url} | {phone}"
            )
        elif isinstance(error, FloodWaitError):
            print(
                f"[!] Лимит запросов к Telegram исчерпан. Жду {error.seconds} сек | {phone}"
            )
            await asyncio.sleep(error.seconds)
        elif isinstance(error, PeerFloodError):
            print(f"[!] Получил спамблок от Telegram | {phone}")
            # self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            # Пробрасываем кастомное исключение
            raise CustomPeerFloodError(phone, error) from error
        elif "Cannot send requests while disconnected" in str(error):
            print(f"[!] Выкинуло из аккаунта, возможно получил бан | {phone}")
            self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
            raise CustomPeerFloodError(phone, error) from error
        else:
            print(f"[!] Неизвестная ошибка: {str(error)} | {phone}")
