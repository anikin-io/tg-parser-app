import asyncio
import itertools
import random
import sys
import time
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.errors import FloodWaitError, PeerFloodError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, ChannelForbidden

from config.chats_keywords_config import (
    BASE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    MIN_MEMBERS,
    SUFFIXES,
)
from config.statuses import STATUS_FREE, STATUS_ON_PAUSE, STATUS_SPAM_BLOCK


class MassParseChatListUseCase:
    def __init__(
        self,
        client_service,
        account_repo,
        csv_repo,
        excel_repo,
        message_utils,
        randomized_utils,
        notification_service,
    ):
        self.client_service = client_service
        self.account_repo = account_repo
        self.csv_repo = csv_repo
        self.excel_repo = excel_repo
        self.message_utils = message_utils
        self.randomized_utils = randomized_utils
        self.notifier = notification_service

        self.active_accounts: Dict[str, TelegramClient] = {}
        self.search_queue = asyncio.Queue()
        self.found_groups = {}
        self.lock = asyncio.Lock()

    MAX_TIME_WAITING = 900

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
        # base_keywords: List[str],
        # suffixes: List[str],
        # exclude_keywords: List[str],
        filename: str,
        # min_members: int,
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
            workers = [
                asyncio.create_task(
                    self._parse_worker(phone, filename, EXCLUDE_KEYWORDS, MIN_MEMBERS)
                )
                for phone in self.active_accounts.keys()
            ]

            await asyncio.gather(*workers)
        except Exception as e:
            parsing_status = "failed"
        finally:
            await self._safe_disconnect_all_accs(STATUS_FREE)

            elapsed_time = time.monotonic() - start_time
            time_str = str(timedelta(seconds=elapsed_time)).split(".")[0]
            await self.notifier.send_parsing_summary(
                time_str, parsing_status, len(self.found_groups)
            )
            await self._save_results(filename)
            await self.notifier.shutdown()

            return time_str, parsing_status, len(self.found_groups)

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

                    full_chat = await client.get_entity(chat.username)
                    if any(kw in full_chat.title.lower() for kw in exclude_keywords):
                        continue

                    chat_full_info = await client(GetFullChannelRequest(full_chat))

                    if self._should_exclude_chat(
                        full_chat, chat_full_info, exclude_keywords, min_members
                    ):
                        continue

                    # if not await self.check_chat_activity(client, full_chat, 30, 10):
                    #     print(
                    #         f"🚫 Чат {full_chat.title} не имеет необходимого числа пользовательского контента"
                    #     )
                    #     continue

                    async with self.lock:
                        self.found_groups[full_chat.id] = {
                            "title": full_chat.title,
                            "username": full_chat.username,
                            "members": chat_full_info.full_chat.participants_count,
                            "link": f"https://t.me/{full_chat.username}",
                            "id": full_chat.id,
                            "about": chat_full_info.full_chat.about or "——",
                        }
                        print(
                            f"✅ Найдена: {full_chat.title} ({chat_full_info.full_chat.participants_count} участника(-ов)) | {phone}"
                        )

                except FloodWaitError as e:
                    raise
                except PeerFloodError as e:
                    raise
                except Exception as e:
                    print(f"⚠️ Ошибка доступа к {chat.username} у {phone}: {str(e)}")
                    continue

                await asyncio.sleep(random.uniform(1, 2))

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
        if self.found_groups:
            csv_path = self.csv_repo.save_groups_to_csv(
                list(self.found_groups.values()), filename
            )
            excel_path = self.excel_repo.save_groups_to_excel(
                list(self.found_groups.values()), filename
            )
            await self.notifier.send_report_files(filename, csv_path, excel_path)

    def _generate_queries(self, base_keywords, suffixes):
        queries = list(
            {
                f"{word} {suffix}".strip().lower()
                for word, suffix in itertools.product(base_keywords, suffixes)
            }
        )
        return queries

    def _should_exclude_chat(
        self, full_chat, chat_full_info, exclude_keywords, min_members
    ):
        if chat_full_info.full_chat.participants_count <= min_members:
            return True
        # Проверка на минус-слова в названии и описании
        title_lower = full_chat.title.lower()
        about_lower = chat_full_info.full_chat.about.lower() or "None"

        excluded_keyword = None
        for keyword in exclude_keywords:
            if keyword in title_lower or keyword in about_lower:
                excluded_keyword = keyword
                break
        if excluded_keyword is not None:
            print(
                f"🚫 Чат {full_chat.title} отфильтрован по минус-слову: {excluded_keyword}"
            )
            return True

    async def check_chat_activity(
        self, client, chat, check_depth=15, min_messages=5
    ) -> bool:
        """
        Проверяет, что в чате есть минимум min_messages пользовательских сообщений на глубине check_depth
        """
        user_messages = 0
        try:
            async for message in client.iter_messages(chat, limit=check_depth):
                if not self.message_utils.is_system_message(message):
                    user_messages += 1
                    if user_messages >= min_messages:
                        return True
            return user_messages >= min_messages
        except Exception as e:
            print(f"⚠️ Ошибка проверки активности чата {chat.title}: {str(e)}")
            return False

    async def _is_valid_chat(self, chat) -> bool:
        # 1. Быстрая проверка на дубликаты (без блокировки)
        async with self.lock:
            if chat.id in self.found_groups:
                return False

        # 2. Проверка типа чата
        if not (
            isinstance(chat, Channel)
            and chat.megagroup
            and not isinstance(chat, ChannelForbidden)
        ):
            return False

        # 3. Публичность (наличие username)
        if not chat.username:
            return False

        # 4. Базовые права доступа
        if chat.default_banned_rights.send_messages or chat.join_request:
            return False

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
