import asyncio
import csv
import logging
import os
import random
from datetime import datetime, timedelta
from os import getenv
from pathlib import Path

import gspread
import portalocker
from aiogram import Bot, Dispatcher
from markdown import markdown

# from opentele.api import API, CreateNewSession, UseCurrentSession
# from opentele.td import TDesktop
# from opentele.tl import TelegramClient
from telethon import errors
from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.sessions import SQLiteSession
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPeerUser, PeerChannel, PeerUser

from .config import config
from .config.messages import MESSAGES
from .core.utils.logger import logger

# re="\033[1;31m"
# ye="\033[1;33m"
# gr="\033[1;32m"
# cy="\033[1;36m"
# SLEEP_TIME = 30

# class main():

#     def banner():
#        with open("system/version", "r") as file:
#           banner_ver = file.read()
#        print(f"{re}╔═╗╔═╗╔═╗╔═╗╔══{cy}╔═╗╔═╗╔═╗╔═╗")
#        print(f"{re}╚═╗║  ╠═╣╠╦╝╠══{cy}╠═╝╠═╣╠╦╝╚═╗")
#        print(f"{re}╚═╝╚═╝╩ ╩╩╚═╚══{cy}╩  ╩ ╩╩╚═╚═╝ " + "v" + banner_ver + "\n")


#     def send_sms():
#         try:
#             cpass = configparser.RawConfigParser()
#             cpass.read('system/config.data')
#             api_id = cpass['cred']['id']
#             api_hash = cpass['cred']['hash']
#             phone = cpass['cred']['phone']
#             proxy_type = cpass['cred']['proxy_type']
#             proxy_ip = cpass['cred']['proxy_ip']
#             proxy_port = int(cpass['cred']['proxy_port'])
#             proxy_username = cpass['cred']['proxy_username']
#             proxy_password = cpass['cred']['proxy_password']
#             if api_id == '':
#                 os.system('clear')
#                 main.banner()
#                 print(re+"[!] Конфиг повреждён или не обнаружен")
#                 input(gr+'['+cy+'+'+gr+']'+cy+" Вернитесь в главное меню и запустите настройку конфига\n")
#                 import start
#                 start.start_up()
#             if api_hash == '':
#                 os.system('clear')
#                 main.banner()
#                 print(re+"[!] Конфиг повреждён или не обнаружен")
#                 input(gr+'['+cy+'+'+gr+']'+cy+" Вернитесь в главное меню и запустите настройку конфига\n")
#                 import start
#                 start.start_up()
#             if phone == '':
#                 os.system('clear')
#                 main.banner()
#                 print(re+"[!] Конфиг повреждён или не обнаружен")
#                 input(gr+'['+cy+'+'+gr+']'+cy+" Вернитесь в главное меню и запустите настройку конфига\n")
#                 import start
#                 start.start_up()
#         except KeyError:
#             os.system('clear')
#             main.banner()
#             print(re+"[!] Конфиг повреждён или не обнаружен")
#             input(re+"[!] Вернитесь в главное меню и запустите настройку конфига\n")
#             import start
#             start.start_up()

#         proxy = None
#         if proxy_type and proxy_ip and proxy_port:
#             proxy = {
#                 'proxy_type': 'socks5',
#                 'addr': proxy_ip,
#                 'port': proxy_port,
#                 'username': proxy_username,
#                 'password': proxy_password,
#                 'rdns': True
#             }
#         client = TelegramClient(phone, api_id, api_hash, proxy=proxy)

#         client.connect()
#         if not client.is_user_authorized():
#             client.send_code_request(phone)
#             os.system('clear')
#             main.banner()
#             client.sign_in(phone, input(gr+'[+] Введите код: '+re))

#         os.system('clear')
#         main.banner()
#         print(gr+'[+] Доступные базы данных:'+re)
#         print(os.listdir('databases/'))
#         m_file = input(gr+"["+ye+"!"+gr+"] Введите название базы для рассылки: "+re)
#         input_file = "databases/"+m_file+".csv"
#         while os.path.isfile(input_file):
#             print((gr+'[+] Выбрана база ')+(re+ m_file+".csv"))
#             users = []
#             # Чтение CSV-файла с участниками и флагом message_sent
#             with open(input_file, encoding='UTF-8') as f:
#                 rows = csv.reader(f, delimiter=",", lineterminator="\n")
#                 next(rows, None)  # Пропускаем заголовок
#                 for row in rows:
#                     if row[6].lower() == 'false':  # Проверка флага message_sent
#                         user = {
#                             'username': row[0],
#                             'id': int(row[1]),
#                             'access_hash': int(row[2]),
#                             'name': row[3],
#                             'message_sent': row[6]  # Сохраняем флаг
#                         }
#                         users.append(user)
#             if not users:
#                 print(re + "[!] Все пользователи уже получили сообщение. Рассылка завершена.")
#                 break

#             print(gr+"[1] Сделать рассылку по userID\n[2] Сделать рассылку по имени")
#             mode = int(input(gr+"Выберите : "+re))

#             print(gr+'[+] Доступные сообщения:'+re)
#             print(os.listdir('messages/'))
#             t_file = input(gr+"[+] Выберите сообщение для рассылки: "+re)
#             # Открываем файл с указанием кодировки UTF-8
#             with open("messages/" + t_file + ".md", 'r', encoding='utf-8') as messagesample:
#                 print((gr+'[+] Выбрано сообщение ')+(re+ t_file+".md"))
#                 # Чтение файла и преобразование markdown в HTML
#                 message_md = messagesample.read()
#                 message_html = markdown(message_md)

#             print(gr+"[+] Установите время между отправкой сообщений (в секундах):")
#             SLEEP_TIME = int(input(gr+"[+] (По-умолчанию 30 секунд) : "+re))

#             for user in users:
#                 if mode == 2:
#                     if user['username'] == "":
#                         continue
#                     receiver = client.get_input_entity(user['username'])
#                 elif mode == 1:
#                     receiver = InputPeerUser(user['id'],user['access_hash'])
#                 else:
#                     print(re+"[!] Неверный режим. Завершаю.")
#                     client.disconnect()
#                     sys.exit()
#                 try:
#                     print(gr+"[+] Отправка сообщения: ", re+ user['name'])
#                     client.send_message(receiver, message_html.format(user['name']), parse_mode='html', link_preview=False)

#                     # Обновляем флаг message_sent на True после успешной отправки
#                     with open(input_file, 'r', encoding='UTF-8') as file:
#                         data = list(csv.reader(file, delimiter=",", lineterminator="\n"))
#                     for row in data:
#                         if row[1] == str(user['id']):
#                             row[6] = 'True'
#                     # Перезаписываем файл с обновленным флагом message_sent
#                     with open(input_file, 'w', encoding='UTF-8', newline='') as file:
#                         writer = csv.writer(file, delimiter=",", lineterminator="\n")
#                         writer.writerows(data)

#                     print((gr+"[+] Ожидаю ") + (re + str(SLEEP_TIME)) + " секунд")
#                     time.sleep(SLEEP_TIME)
#                 except PeerFloodError:
#                     print(re+"[!] Получил предупреждение о спаме от Телеграма. \n[!] Скрипт остановлен. \n[!] Повторите через некоторое время.")
#                     client.disconnect()
#                     sys.exit()
#                 except Exception as e:
#                     print(re+"[!] Ошибка:", e)
#                     print(re+"[!] Пытаюсь продолжить...")
#                     continue
#             os.system('clear')
#             main.banner()
#             client.disconnect()
#             print((gr+"[+] Готово. Сообщение разослано всем пользователям из базы ")+(re+ m_file+".csv"))
#             input(gr+'['+cy+'+'+gr+']'+cy+' Вернуться в главное меню ')
#             import start
#             start.start_up()
#         else:
#             client.disconnect()
#             print((gr+"\n["+re+"!"+gr+"] Указанная база данных не найдена"))
#             print((cy+ "[" + re+ "1" + cy+ "]" + " Повторить"))
#             print((cy+ "[" + re+ "2" + cy+ "]" + " В главное меню"))
#             c_func = input(gr+'['+cy+'+'+gr+']'+cy+' Выберите действие: '+re)
#             if c_func == "1":
#                 main.send_sms()
#             if c_func == "2":
#                 import start
#                 start.start_up()
#             else:
#                 import start
#                 start.start_up()
# main.send_sms()

# Константы для статусов аккаунтов
STATUS_IN_WORK = "в работе"
STATUS_LIMIT_REACHED = "достигнут лимит"
STATUS_SPAM_BLOCK = "спамблок"
STATUS_FREE = "свободен"
STATUS_ON_PAUSE = "на паузе"
# Колонка с датой
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"
# Константы для столбцов
STATUS_COLUMN = 9  # Столбец со статусами
DATE_CONTINUATION_COLUMN = 10  # Столбец с датами продолжения работы
ACCOUNT_NAME_COLUMN = 11
# Указываем путь к JSON-файлу с ключами для сервисного аккаунта
gs = gspread.service_account(filename=os.path.join("config", "creds.json"))
# Открываем таблицу по имени
sheet = gs.open("Accounts").sheet1
# Токен вашего бота, полученный от BotFather
API_TOKEN = config.API_TOKEN
# Идентификатор чата (ваш Telegram ID)
CHAT_ID = config.CHAT_ID
# Создаем объект бота
dp = Dispatcher()

# Настройка логирования
# log_directory = "logs"
# if not os.path.exists(log_directory):
#     os.makedirs(log_directory)
# logging.basicConfig(
#     filename=os.path.join(log_directory, "smsbot.log"),  # Путь к лог-файлу
#     filemode="a",  # Режим добавления (append) в файл
#     format="%(asctime)s - %(levelname)s - %(message)s",  # Формат логов
#     level=logging.INFO,  # Уровень логирования: INFO
#     encoding="utf-8",  # Указываем кодировку UTF-8
# )


def get_account_status(account, sheet):
    row = sheet.find(str(account["phone"])).row  # Ищем строку по телефону
    status = sheet.cell(row, STATUS_COLUMN).value
    date_continuation = sheet.cell(row, DATE_CONTINUATION_COLUMN).value

    if status == STATUS_SPAM_BLOCK:
        # Проверяем дату окончания спамблока
        if date_continuation and datetime.now() >= datetime.strptime(
            date_continuation, DATE_FORMAT
        ):
            sheet.update_cell(
                row, STATUS_COLUMN, STATUS_FREE
            )  # Обновляем статус на "свободен"
            return STATUS_FREE
        else:
            return STATUS_SPAM_BLOCK
    elif status == STATUS_LIMIT_REACHED:
        # Проверяем дату окончания лимита сообщений
        if date_continuation and datetime.now() >= datetime.strptime(
            date_continuation, DATE_FORMAT
        ):
            sheet.update_cell(row, STATUS_COLUMN, STATUS_FREE)
            sheet.update_cell(row, DATE_CONTINUATION_COLUMN, "")  # Очищаем дату
            return STATUS_FREE
        else:
            return STATUS_LIMIT_REACHED
    return status


# Универсальная функция для обновления статуса аккаунта
def update_status(account, sheet, status, hours=None):
    row = sheet.find(str(account["phone"])).row
    sheet.update_cell(row, STATUS_COLUMN, status)

    if status == STATUS_LIMIT_REACHED and hours:
        # Устанавливаем дату возобновления через указанное количество часов (например, 24)
        sheet.update_cell(
            row,
            DATE_CONTINUATION_COLUMN,
            (datetime.now() + timedelta(hours=hours)).strftime(DATE_FORMAT),
        )
    elif status == STATUS_SPAM_BLOCK:
        # Для спамблока дату не трогаем, так как она устанавливается вручную
        sheet.update_cell(row, DATE_CONTINUATION_COLUMN, "")


# Функция для обновления статуса при достижении лимита
def update_status_limit(account, sheet):
    update_status(account, sheet, STATUS_LIMIT_REACHED, hours=24)


def update_status_spam_block(account, sheet):
    update_status(account, sheet, STATUS_SPAM_BLOCK)


# Функция для сброса статусов "в работе" на "свободен"
def reset_in_work_status(sheet):
    accounts = (
        get_accounts_from_google_sheet()
    )  # Получаем все аккаунты из Google Sheets

    for account in accounts:
        row = sheet.find(str(account["phone"])).row
        status = sheet.cell(row, STATUS_COLUMN).value

        # Если статус "в работе", то сбрасываем его на "свободен"
        if status == STATUS_IN_WORK:
            sheet.update_cell(row, STATUS_COLUMN, STATUS_FREE)
            print(MESSAGES["reset_status"].format(phone=account["phone"]))
            # logging.info(MESSAGES["reset_status"].format(phone=account["phone"]))
            logger.info(MESSAGES["reset_status"].format(phone=account["phone"]))


# Функция для выбора свободных аккаунтов
def select_free_accounts(sheet, num_accounts):
    account_configs = (
        get_accounts_from_google_sheet()
    )  # Получаем все аккаунты из Google Sheets
    free_accounts = []

    for account in account_configs:
        status = get_account_status(account, sheet)
        if status == STATUS_FREE:
            free_accounts.append(account)

    # Если количество свободных аккаунтов меньше, чем указано пользователем
    if len(free_accounts) < num_accounts:
        print(MESSAGES["no_free_accounts"].format(available=len(free_accounts)))
        # logging.info(MESSAGES["no_free_accounts"].format(available=len(free_accounts)))
        logger.info(MESSAGES["no_free_accounts"].format(available=len(free_accounts)))
        num_accounts = len(free_accounts)  # Меняем количество на минимальное доступное

    return free_accounts[:num_accounts]


# Функция для получения данных аккаунтов из Google Sheets
def get_accounts_from_google_sheet():
    # TODO: получение данныех из гугл таблиц  идет только 1 раз и глобально

    # Указываем путь к JSON-файлу с ключами для сервисного аккаунта
    # gs = gspread.service_account(filename='creds.json')

    # Открываем таблицу по имени
    # sheet = gs.open("Accounts").sheet1

    # Читаем данные из листа
    accounts = sheet.get_all_records()

    # Форматируем данные в виде списка конфигураций для аккаунтов
    account_configs = []
    for account in accounts:
        account_configs.append(
            {
                "id": str(account["id"]),
                "hash": account["hash"],
                "phone": str(account["phone"]),
                "proxy_type": account["proxy_type"],
                "proxy_ip": account["proxy_ip"],
                "proxy_port": int(account["proxy_port"]),
                "proxy_username": account["proxy_username"],
                "proxy_password": account["proxy_password"],
            }
        )

    return account_configs


# Функция для выбора файла базы данных
def select_database_file():
    files = os.listdir("csv_databases")
    print(MESSAGES["choose_database"])
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    choice = int(input(MESSAGES["input_choice"])) - 1
    return os.path.join("csv_databases", files[choice])


# Функция для отправки уведомления через бота
async def send_notification(message):
    bot = Bot(token=API_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    finally:
        # Закрываем сессию бота после отправки уведомления
        await bot.session.close()


# SESSION_FOLDER = "sessions"
# TDATA_FOLDER = "tdata_folder"

# async def authenticate_account(account):
#     phone = account["phone"]
#     tdata_path = Path(TDATA_FOLDER) / f"{phone}/tdata"
#     session_path = Path(SESSION_FOLDER) / f"{phone}.session"

#     # Используем tdata для существующих аккаунтов
#     if tdata_path.exists() and not session_path.exists():
#         tdesk = TDesktop(tdata_path, api=oldAPI)
#         oldAPI = API.TelegramDesktop.Generate(
#             system="windows", unique_id=str(tdata_path)
#         )

#         # Авторизуемся через Telethon, создаем новую сессию при необходимости
#         client = await tdesk.ToTelethon(
#             session=str(session_path), flag=CreateNewSession, api=oldAPI
#         )

#         newAPI = API.TelegramAndroid.Generate(unique_id=str(session_path))
#         client = await client.QRLoginToNewClient(
#             session="official.session", flag=CreateNewSession, api=newAPI
#         )
#     else:
#         # Создаем новую сессию с API Android
#         newAPI = API.TelegramAndroid.Generate(unique_id=str(session_path))
#         client = await newAPI.ToTelethon(session=str(session_path))

#     # Подключаемся к клиенту
#     await client.connect()
#     await client.PrintSessions()  # Выводим текущие сессии для контроля

#     return client


def get_session_file(phone):
    """Создает имя файла сессии для каждого аккаунта."""
    return os.path.join("sessions", f"{phone}.session")


# Асинхронная функция для отправки сообщений с одного аккаунта
async def send_sms_from_account(account, shared_csv_file, users_queue, sheet):
    status = get_account_status(account, sheet)
    if status != STATUS_FREE:
        print(MESSAGES["user_not_found"].format(name=account["phone"], error=status))
        # logging.warning(
        #     MESSAGES["user_not_found"].format(name=account["phone"], error=status)
        # )
        logger.warning(
            MESSAGES["user_not_found"].format(name=account["phone"], error=status)
        )
        return
    # Устанавливаем статус "в работе"
    row = sheet.find(str(account["phone"])).row
    sheet.update_cell(row, STATUS_COLUMN, STATUS_IN_WORK)
    # Получаем имя аккаунта из таблицы
    account_name = sheet.cell(row, ACCOUNT_NAME_COLUMN).value

    api_id = account["id"]
    api_hash = account["hash"]
    phone = account["phone"]
    proxy_type = account["proxy_type"]
    proxy_ip = account["proxy_ip"]
    proxy_port = int(account["proxy_port"])
    proxy_username = account["proxy_username"]
    proxy_password = account["proxy_password"]

    proxy = None
    if proxy_type and proxy_ip and proxy_port:
        proxy = {
            "proxy_type": "socks5",
            "addr": proxy_ip,
            "port": proxy_port,
            "username": proxy_username,
            "password": proxy_password,
            "rdns": True,
        }

    # Создаем уникальный файл сессии для каждого аккаунта
    session_file = get_session_file(phone)

    async with TelegramClient(
        SQLiteSession(session_file),
        api_id,
        api_hash,
        proxy=proxy,
        device_model="Poco M6 Pro",
        system_version="13",
        app_version="T11.5.3 - P11.16.3",
        lang_code="en",
        system_lang_code="en-US",
    ) as client:
        # if not await client.is_user_authorized():
        #     await client.send_code_request(phone)
        #     await client.sign_in(
        #         phone, input(MESSAGES["request_code"].format(phone=phone))
        #     )
        if not await client.is_user_authorized():

            # Запрос кода авторизации
            await client.send_code_request(phone)

            # Получение кода от пользователя с кастомным сообщением
            code = input(MESSAGES["request_code"].format(phone=phone))

            # Вход с использованием полученного кода
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                # Запрос пароля, если включена двухфакторная аутентификация
                password = input(MESSAGES["request_password"])
                await client.sign_in(password=password)

        # Задержка перед началом отправки сообщений
        await asyncio.sleep(random.uniform(3, 5))

        t_file = "msg copy.md"
        with open("messages/" + t_file, "r", encoding="utf-8") as messagesample:
            message_md = messagesample.read()
            # message_md = message_md.replace("Александр", account_name)
            message_html = markdown(message_md)

        # Лимит на отправку сообщений в день
        message_limit = int(config.MESSAGE_LIMIT)
        messages_sent = 0  # Счетчик отправленных сообщений

        while True:
            if messages_sent >= message_limit:
                # print(f"[!] Лимит сообщений для аккаунта {phone} достигнут. Останавливаю рассылку.")
                print(MESSAGES["message_limit_reached"].format(phone=phone))
                await send_notification(
                    MESSAGES["message_limit_reached"].format(phone=phone)
                )
                # logging.info(MESSAGES["message_limit_reached"].format(phone=phone))
                logger.info(MESSAGES["message_limit_reached"].format(phone=phone))
                update_status_limit(account, sheet)
                break
            # Прерываем цикл, если очередь пуста
            if users_queue.empty():
                break
            user = await users_queue.get()
            if user["message_sent"].lower() == "false":
                receiver = None
                try:
                    # Попытка отправить сообщение по username
                    if user["username"]:
                        try:
                            receiver = await client.get_input_entity(user["username"])
                        except Exception as e:
                            # print(f"[!] Пользователь с username {user['username']} не найден: {e}")
                            print(
                                MESSAGES["not_found_username"].format(
                                    username=user["username"], error=str(e)
                                )
                            )
                            # logging.error(
                            #     MESSAGES["not_found_username"].format(
                            #         username=user["username"], error=str(e)
                            #     )
                            # )
                            logger.error(
                                MESSAGES["not_found_username"].format(
                                    username=user["username"], error=str(e)
                                )
                            )

                    # Если username не найден или отсутствует, пробуем по user_id
                    if not receiver:
                        try:
                            receiver = await client.get_input_entity(
                                PeerUser(user["id"])
                            )
                        except Exception:
                            # print(f"[!] Пользователь с ID {user['id']} не найден напрямую, пробуем через чат")
                            print(
                                MESSAGES["not_found_user_id"].format(user_id=user["id"])
                            )
                            # logging.error(
                            #     MESSAGES["not_found_user_id"].format(user_id=user["id"])
                            # )
                            logger.error(
                                MESSAGES["not_found_user_id"].format(user_id=user["id"])
                            )

                    # Если по user_id не нашли, кешируем участников чата по username группы
                    if not receiver:
                        try:
                            channel = await client.get_input_entity(
                                user["group_username"]
                            )
                            participants = await client.get_participants(channel)
                            for participant in participants:
                                if participant.id == user["id"]:
                                    receiver = await client.get_input_entity(
                                        PeerUser(user["id"])
                                    )
                                    break
                        except Exception as e:
                            # print(f"[!] Не удалось получить участников чата по username группы: {e}")
                            print(
                                MESSAGES["failed_to_get_participants"].format(
                                    error=str(e)
                                )
                            )
                            # logging.error(
                            #     MESSAGES["failed_to_get_participants"].format(
                            #         error=str(e)
                            #     )
                            # )
                            logger.error(
                                MESSAGES["failed_to_get_participants"].format(
                                    error=str(e)
                                )
                            )

                    # Если участник все еще не найден, пробуем вступить в чат через username группы и повторить
                    if not receiver:
                        try:
                            channel = await client.get_input_entity(
                                user["group_username"]
                            )
                            await client(JoinChannelRequest(channel))
                            participants = await client.get_participants(channel)
                            for participant in participants:
                                if participant.id == user["id"]:
                                    receiver = await client.get_input_entity(
                                        PeerUser(user["id"])
                                    )
                                    break
                        except Exception as e:
                            # print(f"[!] Не удалось вступить в чат или получить участников через username группы: {e}")
                            print(
                                MESSAGES["failed_to_join_channel"].format(error=str(e))
                            )
                            # logging.error(
                            #     MESSAGES["failed_to_join_channel"].format(error=str(e))
                            # )
                            logger.error(
                                MESSAGES["failed_to_join_channel"].format(error=str(e))
                            )

                    # Если пользователь найден, отправляем сообщение
                    if receiver:
                        # print(f"[+] Отправка сообщения для: {user['name']} с аккаунта {phone}")
                        await client.send_message(
                            receiver,
                            message_html.format(user["name"]),
                            parse_mode="html",
                            link_preview=False,
                        )
                        print(
                            MESSAGES["start_sending"].format(
                                name=user["name"], phone=phone
                            )
                        )
                        # logging.info(
                        #     MESSAGES["start_sending"].format(
                        #         name=user["name"], phone=phone
                        #     )
                        # )
                        logger.info(
                            MESSAGES["start_sending"].format(
                                name=user["name"], phone=phone
                            )
                        )
                        await send_notification(
                            MESSAGES["start_sending"].format(
                                name=user["name"], phone=phone
                            )
                        )

                        user["message_sent"] = "True"
                        with open(shared_csv_file, "r+", encoding="UTF-8") as f:
                            portalocker.lock(f, portalocker.LOCK_EX)
                            rows = list(csv.reader(f))
                            for row in rows:
                                if row[1] == str(
                                    user["id"]
                                ):  # Или ID, чтобы точно идентифицировать пользователя
                                    row[6] = "True"
                            f.seek(0)
                            writer = csv.writer(f, delimiter=",", lineterminator="\n")
                            writer.writerows(rows)
                            f.truncate()  # Обрезаем файл после записи
                            portalocker.unlock(f)  # Разблокируем файл после завершения

                        # Увеличиваем счетчик сообщений
                        messages_sent += 1

                        sleep_time = random.uniform(30, 60)
                        # print(f"[+] Ожидаю {sleep_time} секунд")
                        print(
                            MESSAGES["waiting"].format(
                                sleep_time=sleep_time, phone=phone
                            )
                        )
                        # logging.info(
                        #     MESSAGES["waiting"].format(
                        #         sleep_time=sleep_time, phone=phone
                        #     )
                        # )
                        logger.info(
                            MESSAGES["waiting"].format(
                                sleep_time=sleep_time, phone=phone
                            )
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        print(
                            MESSAGES["user_not_found_by_username_and_id"].format(
                                name=user["name"]
                            )
                        )
                        # logging.warning(
                        #     MESSAGES["user_not_found_by_username_and_id"].format(
                        #         name=user["name"]
                        #     )
                        # )
                        logger.warning(
                            MESSAGES["user_not_found_by_username_and_id"].format(
                                name=user["name"]
                            )
                        )
                except errors.FloodWaitError as e:
                    print("Have to sleep", e.seconds, "seconds")
                    await asyncio.sleep(e.seconds)
                except PeerFloodError:
                    print(MESSAGES["spam_warning"].format(phone=phone))
                    # logging.warning(MESSAGES["spam_warning"].format(phone=phone))
                    logger.warning(MESSAGES["spam_warning"].format(phone=phone))
                    await send_notification(
                        MESSAGES["spam_warning"].format(phone=phone)
                    )

                    # Если поймали спамблок, обновляем статус на "спамблок"
                    update_status_spam_block(account, sheet)
                    break
                except Exception as e:
                    print(
                        MESSAGES["error"].format(
                            name=user["name"], phone=phone, error=str(e)
                        )
                    )
                    # logging.error(
                    #     MESSAGES["error"].format(
                    #         name=user["name"], phone=phone, error=str(e)
                    #     )
                    # )
                    logger.error(
                        MESSAGES["error"].format(
                            name=user["name"], phone=phone, error=str(e)
                        )
                    )
                    continue


# Функция для запуска рассылки с нескольких аккаунтов
async def distribute_users_among_accounts(sheet):
    account_configs = (
        get_accounts_from_google_sheet()
    )  # Получаем аккаунты из Google Sheets
    free_accounts = select_free_accounts(
        sheet, len(account_configs)
    )  # Получаем только свободные аккаунты
    num_free_accounts = len(free_accounts)
    while True:
        try:
            num_accounts = int(
                input(
                    MESSAGES["input_number_of_accounts"].format(
                        all_accounts=num_free_accounts
                    )
                )
            )  # Запрашиваем количество аккаунтов
            if 1 <= num_accounts <= num_free_accounts:
                break
            else:
                print(f"[!] Пожалуйста, введите число от 1 до {num_free_accounts}.")
        except ValueError:
            print("[!] Пожалуйста, введите корректное число.")

    # Выбор файла базы данных
    shared_csv_file = select_database_file()

    # Чтение пользователей из CSV
    users_queue = asyncio.Queue()
    with open(shared_csv_file, "r", encoding="UTF-8") as f:
        rows = csv.reader(f)
        next(rows)  # Пропускаем заголовок
        for row in rows:
            user = {
                "username": row[0],
                "id": int(row[1]),
                "access_hash": int(row[2]),
                "name": row[3],
                "group_name": row[4],
                "group_username": row[5],
                "message_sent": row[6],
            }
            if (
                user["message_sent"].lower() == "false"
            ):  # Добавляем только тех, кому нужно отправить сообщение
                users_queue.put_nowait(user)
    if users_queue.empty():
        print(MESSAGES["sending_completed"])
        # logging.info(MESSAGES["sending_completed"])
        logger.info(MESSAGES["sending_completed"])
        await send_notification(MESSAGES["sending_completed"])
        return  # Завершаем программу, если все сообщения отправлены

    while True:
        if users_queue.empty():
            print(MESSAGES["sending_completed"])
            # logging.info(MESSAGES["sending_completed"])
            await send_notification(MESSAGES["sending_completed"])
            logger.info(MESSAGES["sending_completed"])
            break  # Завершаем программу, если все сообщения отправлены
        # Получаем свободные аккаунты
        selected_accounts = select_free_accounts(sheet, num_accounts)

        if not selected_accounts:
            print(MESSAGES["no_available_accounts"])
            # logging.info(MESSAGES["no_available_accounts"])
            logger.info(MESSAGES["no_available_accounts"])
            break

        # Запуск рассылки на выбранных аккаунтах
        tasks = [
            send_sms_from_account(account, shared_csv_file, users_queue, sheet)
            for account in selected_accounts
        ]
        await asyncio.gather(*tasks)


# Запуск асинхронной программы
if __name__ == "__main__":
    reset_in_work_status(sheet)
    asyncio.run(distribute_users_among_accounts(sheet))
    reset_in_work_status(sheet)
