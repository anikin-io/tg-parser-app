import asyncio

from telethon import TelegramClient

from core.utils.proxy_utils import ProxyUtils
from infrastructure.converters.tdata_converter import TDataConverter
from infrastructure.repositories.account_repo import AccountRepository
from infrastructure.repositories.session_repo import SessionRepository


class AuthUseCase:

    def __init__(self):
        self.account_repo = AccountRepository()
        self.session_repo = SessionRepository()

    def get_free_accounts(self):
        """Возвращает список свободных аккаунтов из БД."""
        return self.account_repo.get_free_accounts()

    async def authenticate(self, phone: str, proxy: dict = None):
        """
        Для выбранного аккаунта:
         1. Проверяет наличие session-файла (в папке res_sessions).
         2. Если сессии нет, вызывает конвертер tdata → session.
         3. Затем авторизует аккаунт с помощью Telethon.
        Возвращает авторизованный клиент или None при ошибке.
        """

        session_file = self.session_repo.session_exists(phone)

        if not session_file:
            print(
                f"[!] Сессия для {phone} не найдена, требуется конвертация tdata. Запуск конвертации..."
            )
            session_file = await TDataConverter.convert_tdata_to_session(phone, proxy)
            # await asyncio.sleep(1)
            if session_file is None:
                print("[!] Конвертация не удалась.")
                return None
        else:
            print(f"[+] Сессия для {phone} найдена: {session_file}")

            if not await ProxyUtils.check_ip(proxy):
                print(f"[!] Прокси для {phone} нерабочие.")
                return None

        api_data = self.session_repo.get_api_data(phone)
        if not api_data:
            print(f"[!] Не удалось найти API данные для {phone}")
            return None

        client = TelegramClient(
            session=session_file,
            api_id=int(api_data["api_id"]),
            api_hash=api_data["api_hash"],
            device_model=api_data["device_model"],
            system_version=api_data["system_version"],
            app_version=api_data["app_version"],
            lang_code=api_data["lang_code"],
            system_lang_code=api_data["system_lang_code"],
            proxy=proxy,
        )
        await client.connect()
        if not await client.is_user_authorized():
            print(f"[+] Аккаунт {phone} не авторизован. Запрос кода авторизации...")
            await client.send_code_request(phone)
            code = input(f"Введите код для {phone}: ")
            await client.sign_in(phone, code)
        else:
            print(f"[+] Аккаунт {phone} авторизован.")

        return client
