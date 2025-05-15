import asyncio

from core.use_cases.group_parsing_uc import GroupParsingUseCase
from infrastructure.repositories.account_repo import AccountRepository
from interfaces.controllers.auth_controller import AuthController


class ParsGroupController:
    def __init__(self):
        self.auth_controller = AuthController()
        self.account_repo = AccountRepository()

    def get_free_accounts(self):
        return self.account_repo.get_free_accounts()

    async def get_groups_for_account(self, phone: str):
        client = await self.auth_controller.authenticate_account(phone)
        if client is None:
            print("[!] Авторизация не удалась.")
            return None, None
        group_parser = GroupParsingUseCase(client)
        groups = await group_parser.get_groups()
        return groups, client

    async def parse_group_for_account(self, phone: str, group_index: int, client):
        group_parser = GroupParsingUseCase(client)
        result = await group_parser.parse_group(group_index)
        return result
