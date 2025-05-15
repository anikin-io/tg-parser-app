from telethon import TelegramClient


class AuthService:
    def __init__(self, account_repo, session_repo, proxy_utils, converter):
        self.account_repo = account_repo
        self.session_repo = session_repo
        self.proxy_utils = proxy_utils
        self.converter = converter

    async def authenticate(self, phone: str) -> TelegramClient:
        """
        Для выбранного аккаунта:
         1. Проверяет наличие session-файла (в папке res_sessions).
         2. Если сессии нет, вызывает конвертер tdata → session.
         3. Затем авторизует аккаунт с помощью Telethon.
        Возвращает авторизованный клиент или None при ошибке.
        """

        account = self.account_repo.get_account_by_phone(phone)
        if not account:
            print(f"[!] Аккаунт {phone} не найден в БД.")
            return None
        proxy = {
            "proxy_type": "socks5",
            "addr": account.proxy_ip,
            "port": int(account.proxy_port),
            "username": account.proxy_username,
            "password": account.proxy_password,
            "rdns": True,
        }

        session_file = self.session_repo.session_exists(phone)
        if not session_file:
            print(
                f"[!] Сессия для {phone} не найдена, требуется конвертация tdata. Запуск конвертации..."
            )
            session_file = await self.converter.convert_tdata_to_session(phone, proxy)
            # await asyncio.sleep(1)
            if session_file is None:
                print("[!] Конвертация не удалась.")
                return None
        else:
            print(f"[+] Сессия для {phone} найдена: {session_file}")

            if not await self.proxy_utils.check_ip(proxy):
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
            timeout=20,  # увеличено
            connection_retries=7,  # увеличено
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
