import json
import os
import random
import re
import uuid

import phonenumbers
import pycountry
from opentele.api import API, APIData, CreateNewSession
from opentele.td import TDesktop
from opentele.tl import TelegramClient

from config import config
from core.utils.proxy_utils import ProxyUtils


class DeviceParamsGenerator:

    _countries_data = None

    DEVICE_MODELS = {
        # Формат: "Модель": (Вес, [Список API уровней])
        "Samsung Galaxy S23 Ultra": (0.20, [33, 34]),
        "Samsung Galaxy A13 5G": (0.15, [31]),
        "Google Pixel 8 Pro": (0.10, [34]),
        "OnePlus 11 5G": (0.08, [33, 34]),
        "Xiaomi Redmi Note 12 Pro": (0.12, [30, 31]),
        "Poco X5 Pro": (0.10, [31, 33]),
        "Motorola Edge 40": (0.07, [33]),
        "Vivo X90 Pro": (0.05, [33, 34]),
        "Realme GT 3": (0.05, [33]),
        "Poco M6 Pro": (0.08, [33]),
    }

    DESKTOP_MODELS = [
        "Dell XPS 13",
        "HP Spectre x360 14",
        "Lenovo ThinkPad X1 Carbon Gen 11",
        "Microsoft Surface Laptop 6",
        "ASUS ZenBook 14",
        "Acer Swift 5",
        "Dell OptiPlex 7480",
        "HP EliteDesk 800 G9",
        "Lenovo ThinkCentre M90q Gen 4",
        "Microsoft Surface Studio 2",
        "ASUS ROG Strix GA35",
        "Acer Aspire TC-390",
    ]

    # Список поддерживаемых языков Telegram
    SUPPORTED_LANGUAGES = {
        "English",
        "Afrikaans",
        "Albanian",
        "Amharic",
        "Arabic",
        "Azerbaijani",
        "Basque",
        "Belarusian",
        "Bengali",
        "Bulgarian",
        "Burmese",
        "Catalan",
        "Chinese (Simplified)",
        "Chinese (Traditional)",
        "Croatian",
        "Czech",
        "Danish",
        "Dutch",
        "Esperanto",
        "Estonian",
        "Filipino",
        "Finnish",
        "French",
        "Galician",
        "German",
        "Greek",
        "Gujarati",
        "Hebrew",
        "Hindi",
        "Hungarian",
        "Indonesian",
        "Irish",
        "Italian",
        "Japanese",
        "Kannada",
        "Kazakh",
        "Khmer",
        "Korean",
        "Latvian",
        "Lithuanian",
        "Malay",
        "Malayalam",
        "Maltese",
        "Marathi",
        "Norwegian (Bokmål)",
        "Odia",
        "Persian",
        "Polish",
        "Portuguese (Brazil)",
        "Portuguese (Portugal)",
        "Romanian",
        "Russian",
        "Serbian",
        "Slovak",
        "Slovene",
        "Spanish",
        "Swahili",
        "Swedish",
        "Tajik",
        "Tamil",
        "Telugu",
        "Thai",
        "Turkish",
        "Turkmen",
        "Ukrainian",
        "Urdu",
        "Uzbek",
        "Vietnamese",
    }

    # Маппинг кодов языков к официальным названиям
    LANG_MAPPING = {
        "en": "English",
        "af": "Afrikaans",
        "sq": "Albanian",
        "am": "Amharic",
        "ar": "Arabic",
        "az": "Azerbaijani",
        "eu": "Basque",
        "be": "Belarusian",
        "bn": "Bengali",
        "bg": "Bulgarian",
        "my": "Burmese",
        "ca": "Catalan",
        "zh-CN": "Chinese (Simplified)",
        "zh-TW": "Chinese (Traditional)",
        "hr": "Croatian",
        "cs": "Czech",
        "da": "Danish",
        "nl": "Dutch",
        "eo": "Esperanto",
        "et": "Estonian",
        "tl": "Filipino",
        "fi": "Finnish",
        "fr": "French",
        "gl": "Galician",
        "de": "German",
        "el": "Greek",
        "gu": "Gujarati",
        "he": "Hebrew",
        "hi": "Hindi",
        "hu": "Hungarian",
        "id": "Indonesian",
        "ga": "Irish",
        "it": "Italian",
        "ja": "Japanese",
        "kn": "Kannada",
        "kk": "Kazakh",
        "km": "Khmer",
        "ko": "Korean",
        "lv": "Latvian",
        "lt": "Lithuanian",
        "ms": "Malay",
        "ml": "Malayalam",
        "mt": "Maltese",
        "mr": "Marathi",
        "nb": "Norwegian (Bokmål)",
        "or": "Odia",
        "fa": "Persian",
        "pl": "Polish",
        "pt-BR": "Portuguese (Brazil)",
        "pt-PT": "Portuguese (Portugal)",
        "ro": "Romanian",
        "ru": "Russian",
        "sr": "Serbian",
        "sk": "Slovak",
        "sl": "Slovene",
        "es": "Spanish",
        "sw": "Swahili",
        "sv": "Swedish",
        "tg": "Tajik",
        "ta": "Tamil",
        "te": "Telugu",
        "th": "Thai",
        "tr": "Turkish",
        "tk": "Turkmen",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "uz": "Uzbek",
        "vi": "Vietnamese",
    }

    @staticmethod
    def get_random_device():
        return random.choice(DeviceParamsGenerator.DESKTOP_MODELS)

    # @staticmethod
    # def get_random_device():
    #     # Разделяем данные на отдельные списки
    #     devices = list(DeviceParamsGenerator.DEVICE_MODELS.keys())
    #     weights = [v[0] for v in DeviceParamsGenerator.DEVICE_MODELS.values()]
    #     api_versions = [v[1] for v in DeviceParamsGenerator.DEVICE_MODELS.values()]

    #     # Выбираем устройство с учетом весов
    #     chosen_idx = random.choices(range(len(devices)), weights=weights, k=1)[0]
    #     device = devices[chosen_idx]
    #     api_level = random.choice(api_versions[chosen_idx])

    #     return device, f"SDK {api_level}"

    @classmethod
    def _load_countries_data(cls):
        if cls._countries_data is None:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                root_dir = os.path.dirname(os.path.dirname(current_dir))
                data_path = os.path.join(
                    root_dir, "countries_data", "all_countries.json"
                )

                with open(data_path, "r", encoding="utf-8") as f:
                    cls._countries_data = json.load(f)

            except Exception as e:
                print(f"Error loading countries data: {str(e)}")
                cls._countries_data = []

    @staticmethod
    def get_phone_number_lang_code(phone_number):

        DeviceParamsGenerator._load_countries_data()

        try:
            parsed_number = phonenumbers.parse("+" + phone_number, None)
        except phonenumbers.phonenumberutil.NumberParseException:
            return None, None

        country_code = phonenumbers.region_code_for_number(parsed_number)
        if not country_code:
            return None, None

        country_data = None
        for c in DeviceParamsGenerator._countries_data:
            try:
                if c.get("cca2", "").upper() == country_code.upper():
                    country_data = c
                    break
            except AttributeError as e:
                print(f"Invalid country data structure: {str(e)}")
                continue

        if not country_data:
            return None, None

        languages = country_data.get("languages", {})
        if not languages:
            return None, None

        lang_codes_3 = list(languages.keys())
        primary_lang_code_3 = lang_codes_3[0]

        try:
            lang = pycountry.languages.get(alpha_3=primary_lang_code_3)
            lang_code = lang.alpha_2
        except AttributeError:
            return None, None

        system_lang_code = f"{lang_code}-{country_code}"

        # Проверяем поддержку языка
        lang_name = DeviceParamsGenerator.LANG_MAPPING.get(
            system_lang_code, DeviceParamsGenerator.LANG_MAPPING.get(lang_code)
        )

        if lang_name not in DeviceParamsGenerator.SUPPORTED_LANGUAGES:
            return None, None

        return lang_code, system_lang_code


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

        phone_digits = re.sub(r"\D", "", phone)
        session_path = os.path.join(OUTPUT_DIR, f"{phone_digits}.session")
        api_path = os.path.join(OUTPUT_DIR, f"{phone_digits}.json")

        # Генерация рандомных параметров устройства
        device_model = DeviceParamsGenerator.get_random_device()
        lang_code, system_lang_code = DeviceParamsGenerator.get_phone_number_lang_code(
            phone
        )
        if lang_code is None or system_lang_code is None:
            lang_code = "en"
            system_lang_code = "en-US"

        api = APIData(
            api_id=2040,  # API_ID
            api_hash="b18441a1ff607e10a989891a5462e627",  # API_HASH
            device_model=device_model,  # Название устройства
            system_version="Windows 10",  # Версия ОС
            app_version="5.11.1 x64",  # Версия приложения
            lang_code=lang_code,  # Язык клиента
            system_lang_code=system_lang_code,  # Язык системы
            lang_pack="tdesktop",  # Языковой пакет
        )

        # api = APIData(
        #     api_id=35979,  # API_ID
        #     api_hash="fac7419bfbfff19c8241c268017fee2e",  # API_HASH
        #     device_model=device_model,  # Название устройства
        #     system_version=system_version,  # Версия ОС
        #     app_version="T11.5.3 - P11.16.3",  # Версия приложения
        #     lang_code=lang_code,  # Язык клиента
        #     system_lang_code=system_lang_code,  # Язык системы
        #     lang_pack="android",  # Языковой пакет
        # )

        # api = API.TelegramDesktop.Generate(system="windows")
        # temp_name = generate_random_name()

        # temp_api_config_path = os.path.join(OUTPUT_DIR, f"{temp_name}.json")
        with open(api_path, "w", encoding="utf-8") as f:
            json.dump(api.__dict__, f, indent=4)
        print(f"[DEBUG] API-конфигурация сохранена в файл: {api_path}")

        try:
            # temp_session = os.path.join(OUTPUT_DIR, temp_name + ".session")

            tdesk = TDesktop(TDATA_FOLDER)
            print(f"[DEBUG] Loaded accounts: {tdesk.isLoaded()}")

            if proxy and not await ProxyUtils.check_ip(proxy):
                return None

            # client = await tdesk.ToTelethon(
            #     flag=UseCurrentSession, api=api, session=temp_session, proxy=proxy
            # )
            async with await tdesk.ToTelethon(
                flag=CreateNewSession,
                api=api,
                session=session_path,
                password=config.TWOFA_PASSWORD,
                proxy=proxy,
            ) as client:
                print(f"[+] Сессия успешно создана для {phone}")
                return session_path

            # print("[DEBUG] Client после создания:", client)

            # await client.connect()
            # await client.disconnect()
            # await asyncio.sleep(1)

            # phone_digits = re.sub(r"\D", "", phone)
            # new_session_path = os.path.join(OUTPUT_DIR, phone_digits + ".session")
            # if os.path.exists(temp_session):
            #     os.replace(temp_session, new_session_path)
            #     print(f"[+] Успешно! Сессия сохранена в: {new_session_path}")
            # else:
            #     print("[!] Временный файл сессии не найден!")

            # api_config_final_path = os.path.join(OUTPUT_DIR, phone_digits + ".json")
            # os.replace(temp_api_config_path, api_config_final_path)
            # print(
            #     f"[+] Успешно! API-конфигурация переименована в: {api_config_final_path}"
            # )
            # return new_session_path

        except Exception as e:
            print(f"[!] Ошибка: {str(e)}")
            # if "client" in locals() and client is not None:
            #     await client.disconnect()
            if os.path.exists(session_path):
                os.remove(session_path)
            if os.path.exists(api_path):
                os.remove(api_path)
            return None


# Проверка, если файл запущен напрямую
# if __name__ == "__main__":
#     proxy = {
#         "proxy_type": "socks5",
#         "addr": "pool.proxy.market",
#         "port": 10001,
#         "username": "SPeBMFbf42MC",
#         "password": "RNW78Fm5",
#         "rdns": True,
#     }
#     phone = "541139048988"
#     asyncio.run(TDataConverter.convert_tdata_to_session(phone, proxy))
