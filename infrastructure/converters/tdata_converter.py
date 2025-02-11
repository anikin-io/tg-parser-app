import asyncio
import json
import os
import re
import uuid

from opentele.api import API, APIData, UseCurrentSession
from opentele.td import TDesktop
from opentele.tl import TelegramClient

from core.utils.proxy_utils import ProxyUtils


def generate_random_name() -> str:
    return str(uuid.uuid4().hex)[:10]


class TDataConverter:
    @staticmethod
    async def convert_tdata_to_session(phone: str, proxy: dict = None):
        """Конвертирует tdata в session для Telegram. Если конвертация проходит успешно, сессионный файл сохраняется в res_sessions."""

        BASE_DIR = os.getcwd()
        TDATA_FOLDER = os.path.join(BASE_DIR, "tdata_folder", phone, "tdata")
        OUTPUT_DIR = os.path.join(BASE_DIR, "res_sessions")
        os.makedirs(TDATA_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # telegram_desktop_api = APIData(
        #     api_id=611335,  # API_ID
        #     api_hash="d524b414d21f4d37f08684c1df41ac9c",  # API_HASH
        #     device_model="Desktop",  # Название устройства
        #     system_version="Windows 11",  # Версия ОС
        #     app_version="5.10.7 x64",  # Версия приложения
        #     lang_code="ru",  # Язык клиента
        #     system_lang_code="ru-RU",  # Язык системы
        #     lang_pack="tdesktop",  # Языковой пакет (опционально)
        # )
        api = API.TelegramDesktop.Generate(system="windows")
        temp_name = generate_random_name()

        temp_api_config_path = os.path.join(OUTPUT_DIR, f"{temp_name}.json")
        with open(temp_api_config_path, "w", encoding="utf-8") as f:
            json.dump(api.__dict__, f, indent=4)
        print(
            f"[DEBUG] API-конфигурация сохранена во временный файл: {temp_api_config_path}"
        )

        try:
            temp_session = os.path.join(OUTPUT_DIR, temp_name + ".session")

            tdesk = TDesktop(TDATA_FOLDER)
            print(f"[DEBUG] Loaded accounts: {tdesk.isLoaded()}")

            client = await tdesk.ToTelethon(
                flag=UseCurrentSession, api=api, session=temp_session, proxy=proxy
            )
            print("[DEBUG] Client после создания:", client)
            if proxy and not await ProxyUtils.check_ip(proxy):
                return None

            await client.connect()      
            # await client.send_message("me", "Тест: авторизация через session успешна!")

            await client.disconnect()
            await asyncio.sleep(1)
            
            phone_digits = re.sub(r"\D", "", phone)
            new_session_path = os.path.join(OUTPUT_DIR, phone_digits + ".session")
            if os.path.exists(temp_session):
                os.replace(temp_session, new_session_path)
                print(f"[+] Успешно! Сессия сохранена в: {new_session_path}")
            else:
                print("[!] Временный файл сессии не найден!")

            api_config_final_path = os.path.join(OUTPUT_DIR, phone_digits + ".json")
            os.replace(temp_api_config_path, api_config_final_path)
            print(
                f"[+] Успешно! API-конфигурация переименована в: {api_config_final_path}"
            )
            return new_session_path

        except Exception as e:
            print(f"[!] Ошибка: {str(e)}")
            if "client" in locals() and client is not None:
                await client.disconnect()
            if os.path.exists(temp_session):
                os.remove(temp_session)
            if os.path.exists(temp_api_config_path):
                os.remove(temp_api_config_path)
            return None


# Проверка, если файл запущен напрямую
# if __name__ == "__main__":
#     proxy = {
#         "proxy_type": "socks5",
#         "addr": "pool.proxy.market",
#         "port": 10000,
#         "username": "ffEBfQNUesNt",
#         "password": "RNW78Fm5",
#         "rdns": True,
#     }
#     phone = "584128912799"
#     asyncio.run(TDataConverter.convert_tdata_to_session(phone, proxy))
