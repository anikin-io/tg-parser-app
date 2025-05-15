import asyncio
import os
import random
import re
import sys
from contextlib import AsyncExitStack
from datetime import datetime
from typing import Dict, List, Optional, Set
import telethon

import yaml
from cachetools import TTLCache
from telethon import TelegramClient, events, functions
from telethon.errors import (
    AuthKeyInvalidError,
    AuthKeyPermEmptyError,
    AuthKeyUnregisteredError,
    ChannelPrivateError,
    ChatWriteForbiddenError,
    FloodWaitError,
    MsgIdInvalidError,
    PeerFloodError,
    SessionExpiredError,
    SessionRevokedError,
    UserBannedInChannelError,
    UserDeactivatedError,
)
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import (
    DocumentAttributeAnimated,
    DocumentAttributeAudio,
    DocumentAttributeSticker,
    DocumentAttributeVideo,
    MessageMediaContact,
    MessageMediaDocument,
    MessageMediaGeo,
    MessageMediaPhoto,
    MessageMediaPoll,
    MessageMediaVenue,
    MessageMediaWebPage,
)

from config.statuses import STATUS_FREE, STATUS_ON_PAUSE, STATUS_SPAM_BLOCK
from core.domain.exceptions import CustomPeerFloodError

# Константа для определения "долгого" FloodWait
MAX_TIME_WAITING = 900


class AICommentingUseCase:
    def __init__(
        self,
        account_repo,
        client_service,
        blacklist_repo,
        mass_forwarding_uc,
        ai_provider,
        tg_urls_utils,
    ):
        self.account_repo = account_repo
        self.client_service = client_service
        self.mass_forwarding_uc = mass_forwarding_uc
        self.blacklist_repo = blacklist_repo
        self.ai_provider = ai_provider
        self.tg_urls_utils = tg_urls_utils

        config_path = os.path.join("config", "ai_config.yaml")
        channels_file = os.path.join("monitoring_channels", "channels.txt")
        prompts_dir = os.path.join("config", "ai_promts")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.ai_models = self.config.get("ai_models")
        self.prompt_tone = self.config.get("prompt_tone", "хейтер")
        self.comment_limit = self.config.get("comment_limit")
        self.sleep_duration = self.config.get("sleep_duration")
        self.join_channel_delay = self._parse_delay(
            self.config.get("join_channel_delay")
        )
        self.send_message_delay = self._parse_delay(
            self.config.get("send_message_delay")
        )
        self.random_prompt = self.config.get("random_prompt", False)
        self.detect_language = self.config.get("detect_language", False)
        # Чтение базы каналов
        with open(channels_file, "r", encoding="utf-8") as f:
            self.channels = []
            for line in f:
                raw_url = line.strip()
                if not raw_url:
                    continue
                username = self.tg_urls_utils.get_channel_username_by_url(raw_url)
                if username:
                    self.channels.append(username)
        # Чтение промптов
        self.prompts = self._load_prompts(prompts_dir)

        self.comments_sent = {}  # {phone: count}
        self.me_cache = {}  # {phone: me_object}
        self.account_handlers: Dict[str, callable] = {}  # {phone: handler_function}
        self.account_locks: Dict[str, asyncio.Lock] = {}  # {phone: asyncio.Lock()}
        # активные клиенты и их пер‑воркер‑очереди
        self.active_clients: Dict[str, TelegramClient] = {}  # {phone: TelegramClient}
        self.worker_queues: Dict[str, asyncio.Queue] = {}  # очередь на воркера
        # центральная очередь всех постов
        self.post_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        # Сет уже обработанных
        # self.processed_posts: Set[tuple] = set()  # (chat_id, message_id)
        self.processed_posts = TTLCache(
            maxsize=10000, ttl=3600
        )  # maxsize элементов, ttl в секундах
        self.processed_lock = asyncio.Lock()

        self._subscription_queue: asyncio.Queue[str] = (
            asyncio.Queue()
        )  # очередь акков, которым нужно подписаться
        self._subscription_tasks = None  # запускаем фонового подписчика
        self._dispatcher_task = None
        # self._ready_phones: Set[str] = set() # Set акков, у которых уже есть и хендлер, и воркер
        self._ready_phones = list()  # Set акков, у которых уже есть и хендлер, и воркер
        self._ad_pattern = re.compile(
            r"""
                \b
                (erid:?|erid=?|ИНН:?|\#реклама\b|рекламодател[\w-]*)
                \b
            """,
            flags=re.IGNORECASE | re.VERBOSE,
        )

    def _parse_delay(self, delay_str: str):
        """Парсит строку вида '1-5' и возвращает (min, max) как float tuple."""
        try:
            if "-" in delay_str:
                parts = delay_str.split("-")
                return float(parts[0]), float(parts[1])
            else:
                val = float(delay_str)
                return val, val
        except Exception as e:
            print(f"[!] Ошибка парсинга задержки: {str(e)}")
            return 100.0, 200.0

    def _get_random_delay(self, delay_range: tuple):
        return random.uniform(*delay_range)

    def _load_prompts(self, prompts_dir: str):
        prompts = []
        # Если random_prompt = False, сортируем имена файлов
        files = (
            sorted(os.listdir(prompts_dir))
            if not self.random_prompt
            else os.listdir(prompts_dir)
        )
        for filename in files:
            if filename.endswith(".txt"):
                with open(
                    os.path.join(prompts_dir, filename), "r", encoding="utf-8"
                ) as f:
                    prompts.append(f.read())
        return prompts

    def _get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _is_advertisement(self, text: str) -> bool:
        """Возвращает True, если в тексте встречаются маркеры рекламы."""
        return bool(self._ad_pattern.search(text))

    async def initialize_accounts(self, num_accounts: int):
        # Используем уже реализованные методы авторизации из client_service
        free_accounts = self.account_repo.get_free_accounts()[:num_accounts]
        if not free_accounts:
            raise ValueError("Нет свободных аккаунтов")
        tasks = [
            self.client_service.authenticate_and_set_status(acc.phone)
            for acc in free_accounts
        ]
        results = await asyncio.gather(*tasks)
        for acc, client in zip(free_accounts, results):
            if client and not isinstance(client, Exception):
                # self.active_accounts[acc.phone] = client
                self.active_clients[acc.phone] = client
                self.comments_sent[acc.phone] = 0
                self.me_cache[acc.phone] = await client.get_me()
                self.account_locks[acc.phone] = asyncio.Lock()
                self.worker_queues[acc.phone] = (
                    asyncio.Queue()
                )  # CHANGED: создаём per-worker очередь
                print(
                    f"[{self._get_timestamp()}] Аккаунт {acc.phone} успешно подключен и добавлен в очередь."
                )
            else:
                print(f"[!] Не удалось авторизовать аккаунт {acc.phone}")

    async def subscribe_all(self):
        for phone in list(self.active_clients.keys()):
            await self._subscription_queue.put(phone)

    async def _subscription_worker(self):
        """Фоновый таск: подписывает аккаунт и только затем навешивает хендлер и стартует воркер."""
        while True:
            phone = await self._subscription_queue.get()
            client = self.active_clients.get(phone)
            if client:
                try:
                    # 1) сначала подписаться на каналы
                    await self._subscribe_with_replacement(client, phone)
                    # 2) и только после этого — прикрутить прослушивание и воркер
                    await self._attach_handler_for(phone, client)
                    asyncio.create_task(self._worker(phone, client))
                    # теперь аккаунт полностью готов
                    self._ready_phones.append(phone)
                except Exception as e:
                    print(f"[!] Ошибка полного цикла подготовки {phone}: {str(e)}")
            self._subscription_queue.task_done()

    async def _attach_handler_for(self, phone: str, client: TelegramClient):
        """Навешиваем один раз обработчик NewMessage на только что подписавшийся клиент."""
        # если уже был — снимаем
        if phone in self.account_handlers:
            client.remove_event_handler(self.account_handlers[phone])

        async def _handler(event):
            await self._enqueue_post(event)

        client.add_event_handler(_handler, events.NewMessage(chats=self.channels))
        self.account_handlers[phone] = _handler
        print(
            f"[{self._get_timestamp()}] Мониторинг каналов начался для аккаунта {phone}."
        )

    def _post_filter(self, event) -> bool:
        msg = event.message
        chat = event.chat.title or event.chat.id
        if not msg.message:
            print(f"[{self._get_timestamp()}] У поста в {chat} нет текста -> пропуск")
            return False
        replies = getattr(msg, "replies", None)
        if not replies or not getattr(replies, "comments", False):
            print(
                f"[{self._get_timestamp()}] У поста в {chat} закрыты комменты -> пропуск"
            )
            return False
        if self._is_advertisement(msg.message):
            print(
                f"[{self._get_timestamp()}] Обнаружен рекламный пост в {chat} -> пропуск"
            )
            return False
        return True

    async def _subscribe_with_replacement(self, client: TelegramClient, phone: str):
        # Получите актуальные диалоги
        current_dialogs = await client.get_dialogs()
        current_chat_ids = {d.entity.id for d in current_dialogs}
        # Подписываем аккаунт на все каналы из списка с задержкой
        for channel in self.channels:

            try:
                async with self.account_locks.get(phone, asyncio.Lock()):
                    entity = await client.get_entity(channel)
                    cid = entity.id

                    if str(cid) in self.blacklist_repo.get_blacklist(phone):
                        print(
                            f"[{self._get_timestamp()}] Аккаунт {phone} в ЧС у канала {channel} —> пропуск"
                        )
                        continue
                    if cid in current_chat_ids:
                        print(
                            f"[{self._get_timestamp()}] Аккаунт {phone} уже подписан на {channel} —> пропуск"
                        )
                        continue

                    await asyncio.sleep(self._get_random_delay(self.join_channel_delay))
                    await client(JoinChannelRequest(entity))
                    print(
                        f"[{self._get_timestamp()}] Аккаунт {phone} присоединился к каналу {channel}"
                    )

                    # if str(entity.id) in self.blacklist_repo.get_blacklist(phone):
                    #     print(
                    #         f"[{self._get_timestamp()}] Аккаунт {phone} в ЧС у канала {channel} -> пропуск"
                    #     )
                    #     continue

                    # if entity.id not in current_chat_ids:
                    #     await client(JoinChannelRequest(entity))
                    #     print(
                    #         f"[{self._get_timestamp()}] Аккаунт {phone} присоединился к каналу {channel}"
                    #     )
                    # else:
                    #     print(
                    #         f"[{self._get_timestamp()}] Аккаунт {phone} уже подписан на канал {channel}"
                    #     )
            except (
                CustomPeerFloodError,
                PeerFloodError,
                AuthKeyUnregisteredError,
                AuthKeyInvalidError,
                UserDeactivatedError,
                SessionRevokedError,
                SessionExpiredError,
                AuthKeyPermEmptyError,
            ) as e:
                # FULL REPLACEMENT on PeerFlood
                print(f"[!] Бан аккаунта при подписке {phone} -> замена аккаунта")
                await self._replace_full(phone, STATUS_SPAM_BLOCK)
                return
            except FloodWaitError as e:
                if e.seconds > MAX_TIME_WAITING:
                    print(
                        f"[!] Долгий FloodWait при подписке {phone} ({e.seconds}s) -> замена"
                    )
                    await self._replace_full(phone, STATUS_ON_PAUSE)
                    return
                else:
                    print(
                        f"[!] Короткий FloodWait при подписке {phone} ({e.seconds}s) -> сон"
                    )
                    await asyncio.sleep(e.seconds + 1)
            except (ChatWriteForbiddenError, ChannelPrivateError) as e:
                print(
                    f"[!] Аккаунт {phone} забанен (или канал приватный) в {channel}: {str(e)} -> пропускаем"
                )
                self.blacklist_repo.add_to_blacklist(phone, str(entity.id))
                continue
            except Exception as e:
                print(
                    f"[!] Ошибка при подписке {phone} на канал {channel}: {str(e)} -> пропускаем"
                )
                continue
        return

    async def _enqueue_post(self, event):
        mid = event.message.id
        key = (event.chat_id, event.message.id)
        async with self.processed_lock:
            if key in self.processed_posts:
                return
            # self.processed_posts.add(key)
            self.processed_posts[key] = (
                True  # Значение может быть любым, важно наличие ключа
            )

        if not self._post_filter(event):
            return

        # извлекаем данные
        task = {
            "chat_id": event.chat_id,
            "message_id": mid,
            "text": event.message.message,
            "linked_id": None,
            "join_to_send": None,
            "username": event.chat.username or "Private",
            "content_types": self.identify_content_type(event.message),
        }
        full = await event.client(functions.channels.GetFullChannelRequest(event.chat))

        if full.full_chat.linked_chat_id:
            task["linked_id"] = full.full_chat.linked_chat_id
            linked_group = next(
                (c for c in full.chats if c.id == full.full_chat.linked_chat_id),
                None,
            )
            task["join_to_send"] = linked_group.join_to_send
        await self.post_queue.put(task)

    async def _dispatcher(self):
        """
        Распределяет посты из self.post_queue между готовыми воркерами по кругу.
        Если готовых воркеров нет — ждём их появления, не удаляя пост из очереди.
        """
        idx = 0
        while True:
            phones = self._ready_phones
            post = await self.post_queue.get()
            chat_id = post["chat_id"]
            username = post["username"]

            if username not in self.channels:
                self.post_queue.task_done()
                continue  # если канал больше не отслеживается - пропускаем

            # Если нет готовых аккаунтов — вернуть пост и подождать
            if not phones:
                # Пауза, чтобы не заспамить цикл
                await asyncio.sleep(1)
                await self.post_queue.put(post)
                self.post_queue.task_done()
                continue

            # Round-robin, но пропускаем аккаунты, у которых канал в ЧС
            placed = False
            for _ in range(len(phones)):
                phone = phones[idx]
                idx = (idx + 1) % len(phones)
                if str(chat_id) in self.blacklist_repo.get_blacklist(phone):
                    continue  # если в ЧС — пробуем следующий
                await self.worker_queues[phone].put(post)
                placed = True
                break
            if not placed:
                # Все готовые аккаунты забанены в этом канале — безвозвратно пропустить
                print(
                    f"[!] Никто не может обработать пост {post['message_id']} из {chat_id} (все в ЧС) —> пропуск поста"
                )
            self.post_queue.task_done()

    async def _worker(self, phone: str, client: TelegramClient):
        q = self.worker_queues[phone]
        while True:
            post = await q.get()
            try:
                chat_id, mid, text, linked_id, join_to_send, username, content_types = (
                    post["chat_id"],
                    post["message_id"],
                    post["text"],
                    post["linked_id"],
                    post["join_to_send"],
                    post["username"],
                    post["content_types"],
                )

                # if not text:
                #     print(
                #         f"[{self._get_timestamp()}] У поста нет текста, пропускаю | {phone}"
                #     )
                #     continue

                # подготовить prompt
                prompt = self._make_prompt(phone, text, content_types)
                MAX_ATTEMPTS = 3
                success = False
                # До MAX_ATTEMPTS попыток
                for attempt in range(0, MAX_ATTEMPTS):
                    try:
                        comment = await self.ai_provider.gpt_request(
                            prompt, self.ai_models
                        )
                        # response = await self.ai_provider.gpt_request(
                        #     prompt, self.ai_models
                        # )
                        # if response.strip() == "False":
                        #     print(
                        #         f"[{self._get_timestamp()}] Рекламный пост в канале {username} -> пропуск"
                        #     )
                        #     success = True  # чтобы не делать дополнительные попытки
                        #     break
                        # else:
                        #     comment = response
                        # if not comment:
                        #     raise Exception("Empty comment")
                        # join discussion if needed
                        if join_to_send:
                            async with self.account_locks[phone]:
                                await client(JoinChannelRequest(linked_id))
                            print(
                                f"[{self._get_timestamp()}] Аккаунт {phone} вступил в обсуждательный чат {linked_id}"
                            )
                        # send
                        await asyncio.sleep(
                            self._get_random_delay(self.send_message_delay)
                        )
                        async with self.account_locks[phone]:
                            await client.send_message(chat_id, comment, comment_to=mid)
                        print(
                            f"[{self._get_timestamp()}] Комментарий отправлен от аккаунта {phone} в канал {username}"
                        )
                        # Обновляем счётчик комментариев
                        self.comments_sent[phone] += 1
                        # Если достигнут лимит комментариев, делаем паузу
                        if self.comments_sent[phone] >= self.comment_limit:
                            print(
                                f"[{self._get_timestamp()}] Лимит комментов для аккаунта {phone} достигнут -> пауза ({self.sleep_duration} сек.)"
                            )
                            # когда ушёл в спячку
                            self._ready_phones.remove(phone)
                            await asyncio.sleep(self.sleep_duration)
                            self._ready_phones.append(phone)
                            self.comments_sent[phone] = 0

                        success = True
                        break  # успех
                    # except (ChatWriteForbiddenError, ChannelPrivateError):
                    #     # PARTIAL: ban in this channel
                    #     self.blacklist_repo.add_to_blacklist(phone, str(chat_id))
                    #     # print(f"[!] Аккаунт {phone} забанен в канале {chat_id}")
                    #     # alt = self._find_alternative(phone, chat_id)
                    #     # if alt:
                    #     #     phone = alt
                    #     #     client = self.active_clients[alt]
                    #     #     self._ready_phones.append(alt)
                    #     #     continue  # retry with new active
                    #     # else:
                    #     #     print(f"[!] Нет альтернативных аккаунтов для канала {chat_id}")
                    #     #     success = True  # чтобы не срабатывать блок finally
                    #     #     break
                    #     print(
                    #         f"[!] Аккаунт {phone} забанен в канале {username} -> возвращаем задачу в очередь"
                    #     )
                    #     try:
                    #         # если аккаунт всё ещё в канале, покидаем его
                    #         await client(LeaveChannelRequest(channel=chat_id))
                    #         print(
                    #             f"[+] Аккаунт {phone} успешно покинул канал {username}"
                    #         )
                    #     except Exception as leave_err:
                    #         print(
                    #             f"[!] Аккаунту {phone} не удалось покинуть канал {username}: {str(leave_err)}"
                    #         )
                    #     # возврат таска в центральную очередь, чтобы dispatcher мог переназначить
                    #     await self.post_queue.put(
                    #         {
                    #             "chat_id": chat_id,
                    #             "message_id": mid,
                    #             "text": text,
                    #             "linked_id": linked_id,
                    #             "join_to_send": join_to_send,
                    #             "username": username,
                    #             "content_types": content_types,
                    #         }
                    #     )
                    #     # прекращаем обработку этого воркера для данного поста
                    #     success = True
                    #     break
                    except MsgIdInvalidError:
                        print(
                            f"[!] Некорректный ID поста в {username or chat_id} —> пропуск"
                        )
                        success = True
                        break
                    except FloodWaitError as e:
                        if e.seconds > MAX_TIME_WAITING:
                            print(
                                f"[!] Долгий FloodWait при комменте {phone} ({e.seconds} сек.) -> полная замена"
                            )
                            await self._replace_full(phone, STATUS_ON_PAUSE)
                            return
                        else:
                            print(
                                f"[!] Короткий FloodWait при подписке {phone} ({e.seconds} сек.) -> сон"
                            )
                            await asyncio.sleep(e.seconds + 1)
                    except (
                        PeerFloodError,
                        CustomPeerFloodError,
                        AuthKeyUnregisteredError,
                        AuthKeyInvalidError,
                        UserDeactivatedError,
                        SessionRevokedError,
                        SessionExpiredError,
                        AuthKeyPermEmptyError,
                        ChatWriteForbiddenError,
                        ChannelPrivateError,
                    ) as e:
                        print(
                            f"[!] Возможно бан аккаунта при комменте {phone}: {str(e)} -> полная замена"
                        )
                        await self._replace_full(phone, STATUS_SPAM_BLOCK)
                        return
                    except UserBannedInChannelError:
                        print(
                            f"[!] Аккаунту {phone} запрещено писать в супергруппы/каналы: {str(e)} -> полная замена"
                        )
                        await self._replace_full(phone, STATUS_ON_PAUSE)
                        return
                    except Exception as e:
                        if "Cannot send requests while disconnected" in str(e):
                            print(
                                f"[!] Выкинуло из аккаунта, возможно получил бан {phone} -> полная замена"
                            )
                            await self._replace_full(phone, STATUS_SPAM_BLOCK)
                            return

                        print(
                            f"[!] Ошибка отправки коммента, попытка {attempt+1}/{MAX_ATTEMPTS} для {phone}: {str(e)}"
                        )
                        # TODO: возможно надо добавить логику смены на альт-ый акк
                    finally:
                        if attempt == MAX_ATTEMPTS - 1 and not success:
                            print(f"[!] Превышен лимит попыток отправки в {username}")
                            await self._remove_problem_channel(chat_id, username)
            finally:
                q.task_done()

    async def _remove_problem_channel(self, chat_id, username):
        if username in self.channels:
            self.channels.remove(username)
            print(f"[!] Канал {username} удалён из списка отслеживания")
        # Также очищаем из обработанных постов
        # async with self.processed_lock:
        #     self.processed_posts = {
        #         post for post in self.processed_posts if post[0] != chat_id
        #     }
        async with self.processed_lock:
            # обходим копию списка ключей, чтобы безопасно удалять из кэша
            for key in list(self.processed_posts.keys()):
                if key[0] == chat_id:
                    del self.processed_posts[key]

    class SafeDict(dict):
        """Словарь, игнорирующий отсутствующие ключи."""

        def __missing__(self, key):
            return ""

    def _make_prompt(self, phone: str, text: str, content_types: list[str]) -> str:
        template = (
            random.choice(self.prompts) if self.random_prompt else self.prompts[0]
        )

        # content_info = ", ".join(content_types)
        # return template.format(
        #     account_name=self.me_cache.get(phone).first_name,
        #     prompt_tone=self.prompt_tone,
        #     post_text=text,
        #     attachments=content_info,
        # )
        values = {
            "account_name": self.me_cache.get(phone).first_name,
            "prompt_tone": self.prompt_tone,
            "post_text": text,
            "attachments": ", ".join(content_types),
        }

        return template.format_map(self.SafeDict(values))

    def identify_content_type(self, message) -> list[str]:
        """
        Определяет типы вложений в сообщении.
        :param message: объект Telethon Message (event.message)
        :return: список строк, например ['photo', 'video', 'link']
        """
        types = []

        media = message.media

        if not media:
            types.append("Без вложений")
            return types

        # Фото
        if isinstance(media, MessageMediaPhoto):
            types.append("Фото (или картинка)")

        # Документы (включая стикеры, файлы, аудио, видео)
        elif isinstance(media, MessageMediaDocument):
            # Видео
            if any(
                isinstance(attr, DocumentAttributeVideo)
                for attr in media.document.attributes
            ):
                types.append("Видео")
            elif any(
                isinstance(attr, DocumentAttributeAnimated)
                for attr in media.document.attributes
            ):
                types.append("GIF")
            elif any(
                isinstance(attr, DocumentAttributeSticker)
                for attr in media.document.attributes
            ):
                types.append("Стикер")
            # Аудио / голосовые
            elif any(
                isinstance(attr, DocumentAttributeAudio)
                for attr in media.document.attributes
            ):
                types.append("Аудио")
            else:
                types.append("Документ")

        # Ссылка (web preview)
        if isinstance(media, MessageMediaWebPage):
            # WebPage может не содержать preview, но сам факт — ссылка
            types.append("Ссылка")

        if isinstance(media, MessageMediaPoll):
            types.append("Опрос")

        # Геолокация / venue
        if isinstance(media, MessageMediaGeo):
            types.append("Геолокация")
        elif isinstance(media, MessageMediaVenue):
            types.append("Venue")

        # Контакт
        if isinstance(media, MessageMediaContact):
            types.append("Контакт")

        return types

    # def _find_alternative(self, exclude: str, chat_id: int) -> Optional[str]:
    #     for ph in self.active_clients.keys():
    #         if ph == exclude:
    #             continue
    #         if str(chat_id) not in self.blacklist_repo.get_blacklist(ph):
    #             return ph
    #     return None

    async def _replace_full(self, phone: str, status: str):
        # Полная замена аккаунта
        if phone in self._ready_phones:
            self._ready_phones.remove(phone)
        old_client = self.active_clients.pop(phone, None)
        if old_client:
            if phone in self.account_handlers:
                old_client.remove_event_handler(self.account_handlers[phone])
                del self.account_handlers[phone]
            await self._safe_disconnect_account(old_client, phone, status)

        new_phone = await self._pickup_new(status)
        if new_phone:
            # await self._subscribe_with_replacement(client, phone)
            # пушим новый акк в очередь подписки
            await self._subscription_queue.put(new_phone)
            # await self._attach_handlers()
            # asyncio.create_task(self._worker(new, self.active_clients[new]))

    async def _pickup_new(self, status) -> Optional[str]:
        free_accounts = self.account_repo.get_free_accounts()
        if free_accounts:
            for acc in free_accounts:
                if acc.phone not in self.active_clients:
                    client = await self.client_service.authenticate_and_set_status(
                        acc.phone
                    )
                    if isinstance(client, TelegramClient):
                        phone = acc.phone
                        self.active_clients[phone] = client
                        self.account_locks[phone] = asyncio.Lock()
                        self.worker_queues[phone] = asyncio.Queue()
                        self.comments_sent[phone] = 0
                        self.me_cache[phone] = await client.get_me()
                        print(f"[i] Новый аккаунт {phone} взят в работу")
                        return phone
            return None
        else:
            print(
                f"[!] Нет свободных аккаунтов в БД. Активных осталось: {len(self.active_clients)}"
            )
            if not self.active_clients:
                # Если аккаунтов не осталось - завершаем
                print(
                    "[!] Все аккаунты в долгом ожидании или заблокированы. Завершение работы..."
                )
                await self._cancelation_all_tasks()
                await self._safe_disconnect_all_accs(status)
                sys.exit(0)
        return None

    async def _safe_disconnect_account(
        self, client: TelegramClient, phone: str, status: str
    ):
        try:
            await client.disconnect()
            self.account_repo.update_status_by_phone(phone, status)
            self.me_cache.pop(phone, None)
            self.account_locks.pop(phone, None)
            self.comments_sent.pop(phone, None)
            self.worker_queues.pop(phone, None)
            print(f"[✓] Аккаунт {phone} успешно отключен, статус: {status}")
        except Exception as e:
            print(f"[!] Ошибка отключения аккаунта {phone}: {str(e)}")

    async def _safe_disconnect_all_accs(self, status: str):
        """Безопасное отключение всех аккаунтов с обновлением статусов

        :param status: Статус для обновления (например, STATUS_FREE)
        """
        try:
            async with AsyncExitStack() as stack:
                for phone, client in self.active_clients.items():
                    stack.push_async_callback(client.disconnect)
                    self.account_repo.update_status_by_phone(phone, status)
                print(
                    f"[✓] Все подключения безопасно закрыты с установкой статуса '{status}'"
                )
        except Exception as e:
            print(f"[!] Ошибка отключения: {e}")

    async def _cancelation_all_tasks(self):
        # Отменяем все фоновые задачи
        for t in getattr(self, "_subscription_tasks", []):
            t.cancel()
        if hasattr(self, "_dispatcher_task"):
            self._dispatcher_task.cancel()

    async def run(self, count: int):
        await self.initialize_accounts(count)
        await self.subscribe_all()
        # Запускаем фонового подписчика после инициализации
        # self._subscription_tasks = asyncio.create_task(self._subscription_worker())

        # Запускаем несколько подписочных воркеров для параллельной подписки
        self._subscription_tasks = [
            asyncio.create_task(self._subscription_worker())
            for _ in range(len(self.active_clients))
        ]
        self._dispatcher_task = asyncio.create_task(self._dispatcher())
        # for ph, cli in self.active_clients.items():
        #     asyncio.create_task(self._worker(ph, cli))
        try:
            await asyncio.Future()  # держим живым
        except (asyncio.CancelledError, KeyboardInterrupt):
            print("\n[!] Остановка по сигналу, отключаем аккаунты...")
        finally:
            await self._cancelation_all_tasks()
            await self._safe_disconnect_all_accs(STATUS_FREE)
