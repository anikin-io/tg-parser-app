from config.statuses import STATUS_FREE, STATUS_IN_WORK, STATUS_ON_PAUSE


class TelegramClientService:
    def __init__(self, auth_service, account_repo):
        self.auth_service = auth_service
        self.account_repo = account_repo

    async def safe_disconnect(self, client, phone):
        """Безопасное отключение клиента"""
        await client.disconnect()
        self.account_repo.update_status_by_phone(phone, STATUS_FREE)
    
    async def safe_disconnect_with_pause(self, client, phone):
        """Безопасное отключение клиента с установкой статуса НА ПАУЗЕ"""
        await client.disconnect()
        self.account_repo.update_status_by_phone(phone, STATUS_ON_PAUSE)

    async def authenticate_and_set_status(self, phone):
        """Аутентификация и выстановка статуса В РАБОТЕ"""
        try:
            client = await self.auth_service.authenticate(phone)
        except Exception as e:
            print(f"[DEBUG] authenticate({phone}) выбросил {type(e).__name__}: {e}")
            return None

        if client:
            self.account_repo.update_status_by_phone(phone, STATUS_IN_WORK)
            return client
        else:
            return None
