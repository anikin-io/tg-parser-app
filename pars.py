from telethon.sync import TelegramClient, functions
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, ChannelParticipantsSearch
import os, sys
import configparser
import csv
import time
import requests

class main():

    @staticmethod
    def check_ip(proxy=None):
        proxies = {}
        if proxy:
            cpass = configparser.RawConfigParser()
            cpass.read('system/config.data')
            proxy_ip = cpass['cred']['proxy_ip']
            proxy_port = int(cpass['cred']['proxy_port'])-1
            proxy_username = cpass['cred']['proxy_username']
            proxy_password = cpass['cred']['proxy_password']
            proxies = {
                "http": f"http://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}",
                "https": f"https://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}",
            }
        try:
            response = requests.get('http://ip-api.com/json/', proxies=proxies)
            if response.status_code != 200:
                print("[!] Прокси нерабочие. Завершение работы скрипта.")
                sys.exit(1)
            data = response.json()
            city = data.get('city', 'Неизвестно')
            print(f"[+] Проверка IP: {data['query']} (Страна: {data['country']}, Город: {city})")
        # except requests.exceptions.RequestException as e:
        #     print(f"[!] Ошибка при запросе к IP API: {str(e).encode('utf-8', 'replace').decode('utf-8')}")
        #     sys.exit(1)
        except Exception as e:
            print(f"[!] Не удалось проверить IP: {str(e)}")
            sys.exit(1)
    
    @staticmethod
    def parser():
        use_proxy = input("[+] Использовать прокси? (да/нет): ").strip().lower()
        proxy = None
        if use_proxy == 'да':
            cpass = configparser.RawConfigParser()
            cpass.read('system/config.data')
            proxy = {
                'proxy_ip': cpass['cred']['proxy_ip'],
                'proxy_port': cpass['cred']['proxy_port'],
                'proxy_username': cpass['cred']['proxy_username'],
                'proxy_password': cpass['cred']['proxy_password']
            }
            main.check_ip(proxy)
        else:
            main.check_ip()  # Запускаем проверку IP без прокси

        # Подключение к аккаунту
        try:
            cpass = configparser.RawConfigParser()
            cpass.read('system/config.data')
            api_id = cpass['cred']['id']
            api_hash = cpass['cred']['hash']
            phone = cpass['cred']['phone']
        except KeyError:
            print("[!] Ошибка в конфигурации")
            return

        # Настройка прокси для TelegramClient
        proxy_client = None
        if use_proxy == 'да':
            proxy_client = {
                'proxy_type': 'socks5',
                'addr': proxy['proxy_ip'],
                'port': int(proxy['proxy_port']),
                'username': proxy['proxy_username'],
                'password': proxy['proxy_password'],
                'rdns': True
            }

        client = TelegramClient(phone, api_id, api_hash, proxy=proxy_client)
        client.connect()
        
        # main.check_ip()
        # # Подключение к аккаунту
        # try:
        #     cpass = configparser.RawConfigParser()
        #     cpass.read('system/config.data')
        #     api_id = cpass['cred']['id']
        #     api_hash = cpass['cred']['hash']
        #     phone = cpass['cred']['phone']
        #     proxy_type = cpass['cred']['proxy_type']
        #     proxy_ip = cpass['cred']['proxy_ip']
        #     proxy_port = int(cpass['cred']['proxy_port'])
        #     proxy_username = cpass['cred']['proxy_username']
        #     proxy_password = cpass['cred']['proxy_password']

        # except KeyError:
        #     print("[!] Ошибка в конфигурации")
        #     return

        # proxy = None
        # if proxy_type and proxy_ip and proxy_port:
        #     proxy = {
        #         'proxy_type': 'socks5',
        #         'addr': proxy_ip,
        #         'port': proxy_port,
        #         'username': proxy_username,
        #         'password': proxy_password,
        #         'rdns': True
        #     }

        # client = TelegramClient(phone, api_id, api_hash, proxy=proxy)
        # client.connect()

        if not client.is_user_authorized():
            client.send_code_request(phone)
            client.sign_in(phone, input('[+] Введите код: '))

        # Получение списка групп
        chats = []
        groups = []
        result = client(GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=200,
            hash=0
        ))
        chats.extend(result.chats)

        for chat in chats:
            try:
                if chat.megagroup:
                    groups.append(chat)
            except:
                continue

        print('[+] Доступные группы для парсинга:')
        for i, g in enumerate(groups):
            print(f'[{i}] - {g.title}')

        g_index = input("[+] Введите номер группы: ")
        target_group = groups[int(g_index)]

        participant_count = client(functions.channels.GetFullChannelRequest(target_group)).full_chat.participants_count
        print(f"В группе {participant_count} пользователей.")

        all_participants = []
        if participant_count > 10000:
            print('[+] Обработка большой группы...')
            start_time = time.time()  # Начало замера времени
            # Перебор символов для обхода лимита
            alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
            next_char = 'a'  # Начинаем с первого символа
            limit = 200
            all_participants = []  # Список для хранения участников
            unique_ids = set()  # Множество для хранения уникальных идентификаторов

            while next_char:
                offset = 0
                print(f"Ищу участников с логинами, начинающимися на '{next_char}'...")
                
                while True:
                    participants = client(functions.channels.GetParticipantsRequest(
                        channel=target_group,
                        filter=ChannelParticipantsSearch(next_char),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))
                    
                    if not participants.users:
                        break

                    # Добавляем уникальных участников
                    for user in participants.users:
                        if user.id not in unique_ids:
                            unique_ids.add(user.id)  # Добавляем идентификатор в множество
                            all_participants.append(user)  # Добавляем пользователя в список

                    offset += limit

                # Переход к следующему символу
                next_index = alphabet.index(next_char) + 1
                next_char = alphabet[next_index] if next_index < len(alphabet) else None
                end_time = time.time()  # Конец замера времени
                elapsed_time = end_time - start_time  # Время парсинга
        else:
            print('[+] Обработка маленькой группы...')
            start_time = time.time()  # Начало замера времени
            all_participants = client.get_participants(target_group, aggressive=True)
            end_time = time.time()  # Конец замера времени
            elapsed_time = end_time - start_time  # Время парсинга

        print('[+] Сохранение в файл...')
        m_file = input("[+] Введите название файла для сохранения: ")
        with open(f"csv_databases/{m_file}.csv", "w", encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            writer.writerow(['username', 'user_id', 'access_hash', 'name', 'group', 'group_username', 'message_sent'])
            for user in all_participants:
                username = user.username or ""
                name = (user.first_name or "") + " " + (user.last_name or "")
                if not "bot" in username:
                    writer.writerow([username, user.id, user.access_hash, name.strip(), target_group.title, target_group.username, 'False'])

        # Подсчет уникальных участников и процент от общего количества
        unique_count = len(all_participants)
        percentage = (unique_count / participant_count) * 100 if participant_count > 0 else 0
        if elapsed_time >= 60:
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            time_output = f"{int(minutes)} минут(ы) {int(seconds)} секунд(ы)"
        else:
            time_output = f"{int(elapsed_time)} секунд(ы)"

        print(f"[+] Участники группы {target_group.title} сохранены в {m_file}.csv")
        print(f"[+] Время парсинга: {time_output}")
        print(f"[+] Общее количество участников чата: {participant_count}")
        print(f"[+] Количество полученных участников: {unique_count}")
        print(f"[+] Процент полученных участников: {percentage:.2f}%")
        client.disconnect()

main.parser()
