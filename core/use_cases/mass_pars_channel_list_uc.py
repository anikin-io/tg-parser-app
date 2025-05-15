import asyncio
import itertools
import random
import signal
import sys
import time
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.errors import FloodWaitError, PeerFloodError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, ChannelForbidden, ChannelFull

from config.channels_keywords_config import (
    BASE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    MIN_MEMBERS,
    SUFFIXES,
)
from config.statuses import STATUS_FREE, STATUS_ON_PAUSE, STATUS_SPAM_BLOCK


class MassParseChannelListUseCase:
    """
    Парсит публичные каналы Telegram по ключевым словам,
    фильтруя по количеству подписчиков, списку исключений,
    а также проверяет наличие открытых комментариев (дискуссионной группы).
    """

    def __init__(
        self,
        client_service,
        account_repo,
        txt_repo,
        excel_repo,
        message_utils,
        randomized_utils,
        notification_service,
    ):
        self.client_service = client_service
        self.account_repo = account_repo
        self.txt_repo = txt_repo
        self.excel_repo = excel_repo
        self.message_utils = message_utils
        self.randomized_utils = randomized_utils
        self.notifier = notification_service

        self.active_accounts: Dict[str, TelegramClient] = {}
        self.search_queue = asyncio.Queue()
        self.found_channels = {}
        self.lock = asyncio.Lock()
        # для управления фоновыми тасками
        self._worker_tasks: List[asyncio.Task] = []

    MAX_TIME_WAITING = 900

    async def run(self, num_accounts: int, filename: str):
        try:
            await self.initialize(num_accounts)
            return await self.start_parsing(filename)
        except (asyncio.CancelledError, KeyboardInterrupt):
            print("\n[!] Остановка по сигналу…")

    async def _cancel_all_workers(self):
        """
        Корректно дожидаемся отмены всех воркеров
        """
        if not self._worker_tasks:
            return
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def initialize(self, num_accounts: int):
        free_accounts = self.account_repo.get_free_accounts()[:num_accounts]
        if not free_accounts:
            raise ValueError("[!] Нет свободных аккаунтов")

        tasks = [self._authenticate_account(acc.phone) for acc in free_accounts]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _authenticate_account(self, phone: str):
        try:
            client = await self.client_service.authenticate_and_set_status(phone)
            if client:
                self.active_accounts[phone] = client
        except Exception as e:
            print(f"[!] Ошибка авторизации {phone}: {str(e)}")

    async def start_parsing(
        self,
        filename: str,
    ):
        start_time = time.monotonic()
        parsing_status = "completed"
        try:

            queries = self._generate_queries(BASE_KEYWORDS, SUFFIXES)
            for query in queries:
                await self.search_queue.put(query)

            await self.notifier.send_notification(
                f"🚀 Начало парсинга\n"
                f"• Всего запросов: {self.search_queue.qsize()}\n"
                f"• Активных аккаунтов: {len(self.active_accounts)}"
            )

            # Запуск воркеров
            self._worker_tasks = [
                asyncio.create_task(
                    self._parse_worker(phone, filename, EXCLUDE_KEYWORDS, MIN_MEMBERS)
                )
                for phone in self.active_accounts.keys()
            ]

            await asyncio.gather(*self._worker_tasks)
        except Exception as e:
            parsing_status = "failed"
            print(f"[!] Общая ошибка парсинга: {str(e)}")
        finally:
            await self._safe_disconnect_all_accs(STATUS_FREE)
            await self._cancel_all_workers()

            elapsed_time = time.monotonic() - start_time
            time_str = str(timedelta(seconds=elapsed_time)).split(".")[0]
            await self.notifier.send_parsing_summary(
                time_str, parsing_status, len(self.found_channels)
            )
            await self._save_results(filename)
            await self.notifier.shutdown()

            return time_str, parsing_status, len(self.found_channels)

    async def _parse_worker(
        self, phone: str, filename: str, exclude_keywords: List[str], min_members: int
    ):
        client = self.active_accounts[phone]

        while not self.search_queue.empty():
            try:
                # Проверяем что аккаунт все еще активен
                if phone not in self.active_accounts:
                    print(f"[!] Аккаунт {phone} больше не активен")
                    break
                client = self.active_accounts[phone]
                # Проверяем подключение
                if not client.is_connected():
                    print(f"[!] Аккаунт {phone} отключен")
                    break

                query = await self.search_queue.get()

                await self._process_search_query(
                    client, phone, query, exclude_keywords, min_members
                )
                # await asyncio.sleep(self.randomized_utils.get_randomized_delay(10, 5))
                await asyncio.sleep(random.uniform(10, 20))
            except FloodWaitError as e:
                new_phone = await self._handle_flood_wait_error(phone, e, filename)
                if new_phone and new_phone != phone:
                    phone = new_phone
                    client = self.active_accounts.get(new_phone)
                    continue
                else:
                    break
            except PeerFloodError as e:
                new_phone = await self._handle_peer_flood_error(phone, e, filename)
                if new_phone and new_phone != phone:
                    phone = new_phone
                    client = self.active_accounts.get(new_phone)
                else:
                    break
            except Exception as e:
                print(f"[!] Ошибка у {phone}: {str(e)}")
                continue

    async def _process_search_query(
        self,
        client: TelegramClient,
        phone: str,
        query: str,
        exclude_keywords: List[str],
        min_members: int,
    ):
        try:
            if not client.is_connected():
                print(f"[!] Аккаунт {phone} уже отключен")
                return

            result = await client(SearchRequest(q=query, limit=150))
            print(f"🌍 Глобальный поиск: '{query}' | {phone}")
            for chat in result.chats:
                try:
                    if not await self._is_valid_chat(chat):
                        continue

                    full = await client(GetFullChannelRequest(chat))
                    info: ChannelFull = full.full_chat

                    # Фильтры: мин. подписчиков
                    if info.participants_count < min_members:
                        continue

                    # Исключения по словам
                    title = chat.title.lower()
                    about = (info.about or "").lower()
                    if any(kw in title or kw in about for kw in exclude_keywords):
                        continue

                    # Проверка: есть ли обсуждения (open comments)
                    if not info.linked_chat_id:
                        print(f"🚫 Комментарии закрыты в: {chat.title}")
                        continue

                    # if not await self.check_chat_activity(client, full_chat, 30, 10):
                    #     print(
                    #         f"🚫 Чат {full_chat.title} не имеет необходимого числа пользовательского контента"
                    #     )
                    #     continue

                    async with self.lock:
                        self.found_channels[chat.id] = {
                            "title": chat.title,
                            "username": chat.username,
                            "members": info.participants_count,
                            "link": f"https://t.me/{chat.username}",
                            "id": chat.id,
                            "about": info.about or "——",
                        }
                        print(
                            f"✅ Найден: {chat.title} ({info.participants_count} подписчика(-ов)) | {phone}"
                        )

                except FloodWaitError as e:
                    raise
                except PeerFloodError as e:
                    raise
                except Exception as e:
                    print(f"⚠️ Ошибка доступа к {chat.username} у {phone}: {str(e)}")
                    continue

                await asyncio.sleep(random.uniform(2, 3))

        except FloodWaitError as e:
            raise
        except PeerFloodError as e:
            raise
        except Exception as e:
            print(f"🚨 Ошибка поиска у {phone}: {str(e)}")

    async def _handle_flood_wait_error(
        self, phone: str, e: FloodWaitError, filename: str
    ):
        if e.seconds > self.MAX_TIME_WAITING:
            print(f"[!] Долгий FloodWait у {phone} ({e.seconds} сек.), замена аккаунта")
            return await self._replace_account(phone, filename, STATUS_ON_PAUSE)
        else:
            print(f"⏳ Аккаунт {phone} ждет {e.seconds} сек...")
            await asyncio.sleep(e.seconds)
            return phone

    async def _handle_peer_flood_error(
        self, phone: str, e: PeerFloodError, filename: str
    ):
        print(f"[!] Получил спамблок от Telegram | {phone}: {e.message}")
        return await self._replace_account(phone, filename, STATUS_SPAM_BLOCK)

    async def _replace_account(self, phone: str, filename: str, status: str):
        await self._safe_disconnect_account(phone, status, True)
        new_accs = self.account_repo.get_free_accounts()
        if new_accs:
            new_phone = new_accs[0].phone
            await self._authenticate_account(new_accs[0].phone)
            # Проверяем, появился ли новый аккаунт в active_accounts
            if new_phone in self.active_accounts:
                print(f"[+] Аккаунт {new_phone} добавлен в работу")
                return new_phone
            else:
                print(f"[!] Аккаунт {new_phone} не добавлен в работу!")
        else:
            print(
                f"[!] Нет свободных аккаунтов в БД. Активных осталось: {len(self.active_accounts)}"
            )
            if not self.active_accounts:
                # Если аккаунтов не осталось - сохраняем и завершаем
                await self._save_results(filename)
                print(
                    "[!] Все аккаунты в долгом ожидании или заблокированы. Завершение работы..."
                )
                await self._safe_disconnect_all_accs(status)
                sys.exit(0)

        return None

    async def _save_results(self, filename: str):
        if self.found_channels:
            txt_path = self.txt_repo.save_channels_to_txt(
                [ch["link"] for ch in self.found_channels.values()], filename
            )
            excel_path = self.excel_repo.save_groups_to_excel(
                list(self.found_channels.values()), filename
            )
            await self.notifier.send_report_files(filename, txt_path, excel_path)

    def _generate_queries(self, base_keywords, suffixes):
        queries = list(
            {
                f"{word} {suffix}".strip().lower()
                for word, suffix in itertools.product(base_keywords, suffixes)
            }
        )
        return queries

    # def _should_exclude_chat(
    #     self, full_chat, chat_full_info, exclude_keywords, min_members
    # ):
    #     if chat_full_info.full_chat.participants_count <= min_members:
    #         return True
    #     # Проверка на минус-слова в названии и описании
    #     title_lower = full_chat.title.lower()
    #     about_lower = chat_full_info.full_chat.about.lower() or "None"

    #     excluded_keyword = None
    #     for keyword in exclude_keywords:
    #         if keyword in title_lower or keyword in about_lower:
    #             excluded_keyword = keyword
    #             break
    #     if excluded_keyword is not None:
    #         print(
    #             f"🚫 Чат {full_chat.title} отфильтрован по минус-слову: {excluded_keyword}"
    #         )
    #         return True

    # async def check_chat_activity(
    #     self, client, chat, check_depth=15, min_messages=5
    # ) -> bool:
    #     """
    #     Проверяет, что в чате есть минимум min_messages пользовательских сообщений на глубине check_depth
    #     """
    #     user_messages = 0
    #     try:
    #         async for message in client.iter_messages(chat, limit=check_depth):
    #             if not self.message_utils.is_system_message(message):
    #                 user_messages += 1
    #                 if user_messages >= min_messages:
    #                     return True
    #         return user_messages >= min_messages
    #     except Exception as e:
    #         print(f"⚠️ Ошибка проверки активности чата {chat.title}: {str(e)}")
    #         return False

    async def _is_valid_chat(self, chat) -> bool:
        # 1. Быстрая проверка на дубликаты
        async with self.lock:
            if chat.id in self.found_channels:
                return False

        # 2. Проверка типа канала
        if not isinstance(chat, Channel) or isinstance(chat, ChannelForbidden):
            return False
        if not chat.broadcast:
            return False

        # 3. Публичность (наличие username)
        if not chat.username:
            return False

        # 4. Базовые права доступа
        # if chat.default_banned_rights.send_messages or chat.join_request:
        #     return False

        return True

    async def _safe_disconnect_account(
        self, phone: str, status: Optional[str] = None, remove_from_active: bool = True
    ):
        """
        Безопасное отключение конкретного аккаунта
        :param phone: Номер телефона аккаунта
        :param status: Опциональный статус для обновления
        :param remove_from_active: Удалять ли из активных аккаунтов
        """
        client = self.active_accounts.get(phone)

        if not client:
            print(f"[!] Аккаунт {phone} не найден в активных")

        try:
            if client.is_connected():
                await client.disconnect()

            if status is not None:
                self.account_repo.update_status_by_phone(phone, status)

            if remove_from_active and phone in self.active_accounts:
                del self.active_accounts[phone]

            print(
                f"[✓] Аккаунт {phone} безопасно отключен"
                + (f", статус: {status}" if status else "")
            )

        except Exception as e:
            print(f"[!] Ошибка отключения {phone}: {str(e)}")

    async def _safe_disconnect_all_accs(self, status: str):
        """Безопасное отключение всех аккаунтов с опциональным обновлением статусов

        :param status: Статус для обновления (например, STATUS_FREE)
        """
        async with AsyncExitStack() as stack:
            for phone, client in self.active_accounts.items():
                stack.push_async_callback(client.disconnect)
                if status is not None:
                    self.account_repo.update_status_by_phone(phone, status)
            print(
                "[!] Все подключения безопасно закрыты"
                + (f" с установкой статуса |{status}|" if status else "")
            )
