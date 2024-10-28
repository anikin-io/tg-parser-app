# from telethon.sync import TelegramClient, functions
# from telethon.tl.functions.messages import GetDialogsRequest
# from telethon.tl.types import InputPeerEmpty
# import os, sys
# import configparser
# import csv
# import time
# import requests

# re="\033[1;31m"
# gr="\033[1;32m"
# cy="\033[1;36m"

# class main():

#     def banner():
#         with open("system/version", "r") as file:
#             banner_ver = file.read()
#         print(f"{re}╔═╗╔═╗╔═╗╔═╗╔══{cy}╔═╗╔═╗╔═╗╔═╗")
#         print(f"{re}╚═╗║  ╠═╣╠╦╝╠══{cy}╠═╝╠═╣╠╦╝╚═╗")
#         print(f"{re}╚═╝╚═╝╩ ╩╩╚═╚══{cy}╩  ╩ ╩╩╚═╚═╝ " + "v" + banner_ver + "\n")

#     def check_ip():
#         proxies = {
#             "http": "http://HNwbG7Ta:p3GLfvVr@154.210.87.53:63802",
#             "https": "https://HNwbG7Ta:p3GLfvVr@154.210.87.53:63802",
#         }
#         try:
#             # Отправляем запрос на сервис для проверки IP
#             response = requests.get('http://ip-api.com/json/', proxies=proxies)
#             data = response.json()
#             print(f"Проверка IP: {data['query']} (Страна: {data['country']})")
#         except Exception as e:
#             print(f"Не удалось проверить IP: {str(e)}")

#     def parser():
#         main.check_ip()  # Проверяем IP до подключения к Telegram

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
#         chats = []
#         last_date = None
#         chunk_size = 200
#         groups=[]
 
#         result = client(GetDialogsRequest(
#                     offset_date=last_date,
#                     offset_id=0,
#                     offset_peer=InputPeerEmpty(),
#                     limit=chunk_size,
#                     hash = 0
#                 ))
#         chats.extend(result.chats)
 
#         for chat in chats:
#             try:
#                 if chat.megagroup== True:
#                     groups.append(chat)
#             except:
#                 continue
 
#         print(gr+'[+] Доступные группы для парсинга:'+re)
#         i=0
#         for g in groups:
#             print(gr+'['+cy+str(i)+gr+']'+cy+' - '+ g.title)
#             i+=1
 
#         print('')
#         g_index = input(gr+"[+] Введите номер группы для выбора: "+re)
#         try:
#             target_group=groups[int(g_index)]
#         except (IndexError, ValueError):
#             client.disconnect()
#             print((gr+"\n["+re+"!"+gr+"] Указанная группа не найдена"))
#             print((cy+ "[" + re+ "1" + cy+ "]" + " Повторить"))
#             print((cy+ "[" + re+ "2" + cy+ "]" + " В главное меню"))
#             c_func = input(gr+'['+cy+'+'+gr+']'+cy+' Выберите действие: '+re)
#             if c_func == "1":
#                 main.parser()
#             if c_func == "2":
#                 import start
#                 start.start_up()
#             else:
#                 import start
#                 start.start_up()

#         g_name = target_group.title
 
#         print(gr+'[+] Собираю данные участников...')
#         time.sleep(1)
#         all_participants = []
#         all_participants = client.get_participants(target_group, aggressive=True)
      
#         print(gr+'[+] Сохраняю в файл...')
#         time.sleep(1)
#         m_file = input(gr+"[+] Введите название базы для сохранения: "+re)
#         with open("databases/"+m_file+".csv","w",encoding='UTF-8') as f:
#             writer = csv.writer(f,delimiter=",",lineterminator="\n")
#             writer.writerow(['username','user id', 'access hash','name','group', 'group username', 'message_sent'])
#             for user in all_participants:
#                 if user.username:
#                     username = user.username
#                 else:
#                     username = ""
#                 if user.first_name:
#                     first_name = user.first_name
#                 else:
#                     first_name = ""
#                 if user.last_name:
#                     last_name= user.last_name
#                 else:
#                     last_name= ""
#                 name = (first_name + ' ' + last_name).strip()
#                 if "Bot" in username:
#                     writer.writerow('\n')
#                 else:
#                     writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.username, 'False'])
#         file_path = os.path.dirname(__file__)
#         os.system('clear')
#         main.banner()    
#         print((gr+"[+] Участники группы ")+(re+ g_name)+(gr+" сохранены в базу ")+(re+ m_file+".csv"))
#         client.disconnect()
#         input(gr+'['+cy+'+'+gr+']'+cy+' Вернуться в главное меню ')
#         import start
#         start.start_up()
# main.parser()

# import os
# import csv
# import time
# import configparser
# from telethon import TelegramClient
# from telethon.tl.functions.messages import GetDialogsRequest
# from telethon.tl.types import InputPeerEmpty,InputPeerChannel, InputPeerChat, Channel, Chat

# class TelegramParser:
#     def __init__(self):
#         self.accounts = self.load_accounts()

#     def load_accounts(self):
#         """Загружаем данные из нескольких конфиг файлов"""
#         accounts = []
#         for filename in os.listdir('accs/'):
#             if filename.endswith('.data'):
#                 cpass = configparser.RawConfigParser()
#                 cpass.read(f'system/{filename}')
#                 api_id = cpass['cred']['id']
#                 api_hash = cpass['cred']['hash']
#                 phone = cpass['cred']['phone']
#                 proxy_type = cpass['cred']['proxy_type']
#                 proxy_ip = cpass['cred']['proxy_ip']
#                 proxy_port = int(cpass['cred']['proxy_port'])
#                 proxy_username = cpass['cred']['proxy_username']
#                 proxy_password = cpass['cred']['proxy_password']
#                 accounts.append({
#                     'api_id': api_id,
#                     'api_hash': api_hash,
#                     'phone': phone,
#                     'proxy': {
#                         'proxy_type': 'socks5',
#                         'addr': proxy_ip,
#                         'port': proxy_port,
#                         'username': proxy_username,
#                         'password': proxy_password,
#                         'rdns': True
#                     }
#                 })
#         return accounts

#     async def get_chat_choice(self, client):
#         """Выбор чата для парсинга"""
#         chats = []
#         groups = []
#         result = await client(GetDialogsRequest(
#             offset_date=None,
#             offset_id=0,
#             offset_peer=InputPeerEmpty(),
#             limit=200,
#             hash=0
#         ))
#         chats.extend(result.chats)
#         for chat in chats:
#             if getattr(chat, 'megagroup', False):
#                 groups.append(chat)
        
#         print('Доступные группы для парсинга:')
#         for i, group in enumerate(groups):
#             print(f"[{i}] {group.title}")
        
#         while True:
#             try:
#                 g_index = input("Введите номер группы для выбора: ")
#                 if g_index.strip() == "":
#                     print("Ошибка: Ввод не может быть пустым. Пожалуйста, введите номер группы.")
#                     continue
#                 g_index = int(g_index)  # Пробуем преобразовать в int
#                 if 0 <= g_index < len(groups):
#                     return groups[g_index]
#                 else:
#                     print("Ошибка: Введен неверный номер группы. Попробуйте еще раз.")
#             except ValueError:
#                 print("Ошибка: Введено не числовое значение. Пожалуйста, введите номер группы.")
#         # g_index = int(input("Введите номер группы для выбора: "))
#         # return groups[g_index]

#     async def parse_group(self, account, target_group):
#         """Асинхронный парсинг группы с сохранением результатов в файл"""
#         client = TelegramClient(account['phone'], account['api_id'], account['api_hash'], proxy=account['proxy'])
#         await client.start()

#                 # Проверка типа target_group и приведение к нужному типу
#         if isinstance(target_group, InputPeerChannel):
#             target_group = InputPeerChannel(target_group.id, target_group.access_hash)
#         elif isinstance(target_group, InputPeerChat):
#             target_group = InputPeerChat(target_group.id)

#         # Попробуйте получить участников
#         try:
#             all_participants = await client.get_participants(target_group, aggressive=True)
#         except Exception as e:
#             print(f"Ошибка при получении участников: {e}")
#             return

#         file_name = f"temp/{target_group.username}_{account['phone']}.csv"

#         with open(file_name, 'w', encoding='UTF-8') as f:
#             writer = csv.writer(f,delimiter=",",lineterminator="\n")
#             writer.writerow(['username', 'user id', 'access hash', 'name', 'group', 'group username', 'message_sent'])
#             for user in all_participants:
#                 if user.username:
#                     username = user.username
#                 else:
#                     username = ""
#                 if user.first_name:
#                     first_name = user.first_name
#                 else:
#                     first_name = ""
#                 if user.last_name:
#                     last_name= user.last_name
#                 else:
#                     last_name= ""
#                 name = (first_name + ' ' + last_name).strip()
#                 if "Bot" in username:
#                     writer.writerow('\n')
#                 else:
#                     writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.username, 'False'])
        
#         await client.disconnect()
#         print(f"Участники сохранены в файл {file_name}")

#     def merge_files(self, output_file):
#         """Объединение файлов и удаление дубликатов"""
#         unique_entries = {}
#         files = [f for f in os.listdir('temp/') if f.endswith('.csv')]

#         for file in files:
#             with open(f'temp/{file}', 'r', encoding='UTF-8') as f:
#                 reader = csv.reader(f)
#                 next(reader)  # Пропустить заголовок
#                 for row in reader:
#                     if len(row) < 6:  # Проверяем, что в строке достаточно элементов
#                         continue  # Пропускаем строки с недостаточным количеством элементов
                    
#                     # Создаем уникальный ключ, игнорируя access hash
#                     key = (row[0] or '',  # username
#                         row[1],  # user id
#                         row[3] or '',  # name
#                         row[4],  # group
#                         row[5])  # group username

#                     if key not in unique_entries:
#                         unique_entries[key] = row  # Сохраняем полную строку

#         with open(output_file, 'w', encoding='UTF-8') as f:
#             writer = csv.writer(f, delimiter=",", lineterminator="\n")
#             writer.writerow(['username', 'user id', 'access hash', 'name', 'group', 'group username', 'message_sent'])

#             for entry in unique_entries.values():
#                 writer.writerow(entry)  # Записываем уникальные строки

#         print(f"Итоговый файл сохранен как {output_file}")

#     async def run(self):
#         """Основной процесс парсинга"""
#         target_group = None
#         for account in self.accounts:
#             print(f"\nВход в аккаунт {account['phone']}...")
#             client = TelegramClient(account['phone'], account['api_id'], account['api_hash'], proxy=account['proxy'])
#             await client.start()
#             target_group = await self.get_chat_choice(client)
#             await client.disconnect()
#             await self.parse_group(account, target_group)

#         output_file = input("Введите название итогового файла (без расширения): ") + '.csv'
#         self.merge_files(f"databases/{output_file}")

# if __name__ == "__main__":
#     parser = TelegramParser()
#     import asyncio
#     asyncio.run(parser.run())

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
        with open(f"databases/{m_file}.csv", "w", encoding='UTF-8') as f:
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
