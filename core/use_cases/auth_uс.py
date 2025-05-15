import asyncio

from telethon import TelegramClient

from core.utils.proxy_utils import ProxyUtils
from infrastructure.converters.tdata_converter import TDataConverter
from infrastructure.repositories.account_repo import AccountRepository
from infrastructure.repositories.session_repo import SessionRepository


class AuthUseCase:

    def __init__(self, auth_service, account_repo):
        self.auth_service = auth_service
        self.account_repo = account_repo

    def get_free_accounts(self):
        """Возвращает список свободных аккаунтов из БД."""
        return self.account_repo.get_free_accounts()

    async def authenticate(self, phone: str):
        client = await self.auth_service.authenticate(phone)
        return client
