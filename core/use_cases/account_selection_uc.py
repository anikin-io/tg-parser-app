from infrastructure.repositories.account_repo import AccountRepository


class AccountSelectionUseCase:
    """Логика выбора аккаунта из БД"""

    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    # def add_account(
    #     self, phone, name, proxy_ip, proxy_port, proxy_username, proxy_password, status
    # ):
    #     """Добавляет новый аккаунт в БД"""
    #     self.account_repo.add_account(
    #         phone, name, proxy_ip, proxy_port, proxy_username, proxy_password, status
    #     )

    # def get_all_accounts(self):
    #     """Получает список всех аккаунтов."""
    #     return self.account_repo.get_all_accounts()

    def get_free_accounts(self):
        """Получает список свободных аккаунтов"""
        return self.account_repo.get_free_accounts()

    # def search_account_by_phone(self, phone):
    #     """Ищет аккаунт по номеру телефона."""
    #     return self.account_repo.get_account_by_phone(phone)

    # def change_status(self, phone, new_status):
    #     """Меняет статус аккаунта по номеру телефона"""
    #     self.account_repo.update_status_by_phone(phone, new_status)

    # def change_status_to_free(self):
    #     """Изменяет статус всех аккаунтов с 'в работе' на 'свободен'."""
    #     self.account_repo.reset_status_to_free()
