import asyncio
from core.use_cases.auth_uс import AuthUseCase

class AuthController:
    def __init__(self):
        self.use_case = AuthUseCase()
    
    def get_free_accounts(self):
        """Возвращает список свободных аккаунтов (сущности Account)."""
        return self.use_case.get_free_accounts()
    
    async def authenticate_account(self, phone: str):
        """
        Подготавливает аккаунт: проверка наличия session, конвертация (при необходимости) и авторизация. Возвращает объект TelegramClient.
        """
        return await self.use_case.authenticate(phone)
