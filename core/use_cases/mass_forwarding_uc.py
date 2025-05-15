import asyncio
import sys
from contextlib import AsyncExitStack
from typing import Dict, Optional

from telethon import TelegramClient, functions
from telethon.errors import ChatWriteForbiddenError, UserBannedInChannelError
from telethon.tl.functions.channels import JoinChannelRequest

from config.constants import FORWARD_DELAY, JOIN_DELAY, LOOP_INTERVAL
from config.statuses import STATUS_FREE, STATUS_SPAM_BLOCK
from core.domain.exceptions import CustomPeerFloodError


class MassForwardUseCase:
    def __init__(
        self,
        error_handler_service,
        client_service,
        forwarding_uc,
        account_repo,
        randomized_utils,
        tg_urls_utils,
        csv_repo,
    ):

        self.error_handler_service = error_handler_service
        self.client_service = client_service
        self.forwarding_uc = forwarding_uc
        self.account_repo = account_repo
        self.randomized_utils = randomized_utils
        self.tg_urls_utils = tg_urls_utils
        self.csv_repo = csv_repo

        self.active_accounts: Dict[str, TelegramClient] = {}
        self.shared_queue = asyncio.Queue()
        self.current_loop = 0

    async def initialize(self, num_accounts: int):
        free_accounts = self.account_repo.get_free_accounts()[:num_accounts]
        if not free_accounts:
            raise ValueError("[!] Нет свободных аккаунтов")

        # Асинхронная инициализация аккаунтов
        tasks = [
            self.forwarding_uc._authenticate_and_prepare(acc.phone)
            for acc in free_accounts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_num_accounts = num_accounts
        # Фильтруем успешно инициализированные аккаунты
        for acc, result in zip(free_accounts, results):
            if not isinstance(result, Exception):
                self.active_accounts[acc.phone] = result
                # self.account_repo.update_status_by_phone(acc.phone, STATUS_IN_WORK)
            else:
                total_num_accounts -= 1
                print(
                    f"[!] Аккаунт {acc.phone} не удалось авторизовать. Будет использовано {total_num_accounts} аккаутна(ов)"
                )
                continue

    async def process_mass_forward(
        self,
        choice_csv_file: int,
        csv_files: list[str],
        source_channel_url: str,
        message_id: int,
        join_groups: bool,
        subscribe_channel: Optional[str] = None,
    ):
        # Загрузка данных из CSV
        csv_file_path = self.csv_repo.choice_csv_file(choice_csv_file, csv_files)
        chat_data = self.csv_repo.read_chat_data(csv_file_path)

        # Заполнение очереди только неотправленными сообщениями
        for chat in chat_data:
            if not chat["message_sent"]:
                await self.shared_queue.put(chat)

        source_chat_id = self.tg_urls_utils.get_channel_id_by_url(source_channel_url)

        # Основной цикл обработки
        while not self.shared_queue.empty():
            await self._distribute_tasks(
                source_chat_id,
                message_id,
                join_groups,
                subscribe_channel,
                csv_file_path,
            )

            if LOOP_INTERVAL >= 0:
                self.current_loop += 1
                print(f"[✓] Завершился цикл №{self.current_loop}")
                await self.forwarding_uc._handle_loop_delay()
                await self._reset_queue(csv_file_path)
            else:
                await self._safe_disconnect_all_accs(STATUS_FREE)
                break

    async def _distribute_tasks(
        self, source_chat_id, message_id, join_groups, subscribe_channel, csv_path
    ):
        workers = []
        for phone, client in self.active_accounts.items():
            worker = asyncio.create_task(
                self._worker_task(
                    client,
                    phone,
                    source_chat_id,
                    message_id,
                    join_groups,
                    subscribe_channel,
                    csv_path,
                )
            )
            workers.append(worker)

        await asyncio.gather(*workers)

    async def _worker_task(
        self,
        client: TelegramClient,
        phone: str,
        source_chat_id: int,
        message_id: int,
        join_groups: bool,
        subscribe_channel: Optional[str],
        csv_path: str,
    ):
        # Подписка на канал если требуется
        # if subscribe_channel:
        #     subscription_result = await self._subscribe_to_channel(
        #         client, phone, subscribe_channel
        #     )
        #     if not subscription_result:
        #         return
        # try:
        #     current_dialogs = await client.get_dialogs()
        #     current_chat_ids = {d.entity.id for d in current_dialogs}
        #     # current_chat_ids = None
        # except:
        #     print(f"[!] Произошла ошибка получения диалогов: {str(e)} | {phone}")
        #     return

        # Первичная инициализация: подписка и получение диалогов
        client, current_chat_ids = await self._reinitialize_account(
            phone, subscribe_channel
        )
        if not client:
            print(f"[!] Ошибка инициализации для аккаунта {phone}")
            return

        while not self.shared_queue.empty():
            try:
                # Проверка актуальности аккаунта перед каждой итерацией
                if phone not in self.active_accounts:
                    print(f"[!] Аккаунт {phone} больше не активен")
                    break
                client = self.active_accounts[phone]
                if not client.is_connected():
                    print(f"[!] Аккаунт {phone} отключен")
                    break

                chat_task = await self.shared_queue.get()

                if chat_task["message_sent"]:
                    continue

                # Вступление в группу если требуется
                # if join_groups:
                entity, topic_id = await self.forwarding_uc._process_single_chat(
                    client, phone, chat_task["link"], current_chat_ids
                )
                await asyncio.sleep(
                    self.randomized_utils.get_randomized_delay(JOIN_DELAY, 5)
                )
                if not entity:
                    continue

                # Пересылка сообщения
                result_of_forwarding = await self.forwarding_uc._forward_single_message(
                    client, phone, source_chat_id, message_id, entity, topic_id
                )

                if result_of_forwarding:
                    await self.csv_repo.mark_as_sent(csv_path, chat_task["link"])
                else:
                    continue

                await asyncio.sleep(
                    self.randomized_utils.get_randomized_delay(FORWARD_DELAY, 5)
                )
            except CustomPeerFloodError as e:
                # new_phone = await self._handle_peer_flood_error(phone, e)
                new_phone = await self._replace_banned_account(phone, STATUS_SPAM_BLOCK)
                if new_phone and new_phone != phone:
                    phone = new_phone
                    client, current_chat_ids = await self._reinitialize_account(
                        phone, subscribe_channel
                    )
                    if not client:
                        break
                    continue
                else:
                    break
            except Exception as e:
                print(f"[!] Произошла ошибка: {str(e)} | {phone}")
                continue

    async def _reinitialize_account(
        self, phone: str, subscribe_channel: Optional[str]
    ) -> tuple[Optional[TelegramClient], Optional[set]]:
        """
        Повторно инициализирует аккаунт: выполняет подписку (если требуется) и получает текущие диалоги.
        Возвращает обновлённого клиента и множество текущих ID диалогов.
        """
        if phone not in self.active_accounts:
            print(f"[!] Аккаунт {phone} не найден для реинициализации")
            return None, None

        client = self.active_accounts[phone]

        # Получите актуальные диалоги
        current_dialogs = await client.get_dialogs()
        current_chat_ids = {d.entity.id for d in current_dialogs}
        # Выполните подписку, если требуется
        if subscribe_channel:
            subscription_result = await self._subscribe_to_channel(
                client, phone, subscribe_channel, current_chat_ids
            )
            if not subscription_result:
                return None, None

        return client, current_chat_ids

    async def _subscribe_to_channel(
        self, client: TelegramClient, phone: str, channel_url: str, existing_chats
    ):
        try:
            entity = await client.get_entity(channel_url)

            # Проверяем, подписан ли уже аккаунт
            # dialogs = await client.get_dialogs()
            # existing_chats = {d.entity.id for d in dialogs}

            if entity.id not in existing_chats:
                await client(JoinChannelRequest(entity))
                print(f"[✓] Подписался на {channel_url} | {phone}")
            else:
                print(f"[✓] Уже подписан на {channel_url} | {phone}")

            return True
        except Exception as e:
            await self.error_handler_service._handle_join_errors(e, phone, channel_url)
            return False

    # async def _join_group(self, client: TelegramClient, group_url: str):
    #     try:
    #         base_url, topic_id = TelegramUrlsUtils.parse_chat_link(group_url)
    #         entity = await client.get_entity(base_url)
    #         await client(JoinChannelRequest(entity))
    #         return {"entity": entity, "topic_id": topic_id}
    #     except Exception as e:
    #         print(f"Join group error: {e}")
    #         return None

    # async def _forward_message(
    #     self, client, source_chat, msg_id, target, topic_id=None
    # ):
    #     try:
    #         await client.forward_messages(
    #             target["entity"],
    #             msg_id,
    #             from_peer=source_chat,
    #             send_as=target.get("topic_id"),
    #         )
    #         return True
    #     except Exception as e:
    #         print(f"Forward error: {e}")
    #         return False

    async def _forward_message(
        self,
        client: TelegramClient,
        source_chat_id,
        message_id,
        entity,
        topic_id,
        phone,
    ):

        try:
            me = await client.get_me()
            my_id = me.id
            last_msg = await client.get_messages(entity, limit=1)
            if last_msg and last_msg[0].sender_id == my_id:
                print(f"[!] Последнее сообщение в {entity.title} наше, пропускаю")
                return
        except Exception as e:
            print(f"[!] Ошибка проверки сообщений в {entity.title}: {e}")

        if not await self.forwarding_uc._check_chat_permissions(client, entity):
            return

        try:
            if topic_id:
                await client(
                    functions.messages.ForwardMessagesRequest(
                        from_peer=source_chat_id,
                        id=[message_id],
                        to_peer=entity,
                        top_msg_id=topic_id,
                    )
                )
            else:
                await client.forward_messages(
                    entity, message_id, from_peer=source_chat_id
                )

            print(
                f"[✓] Успешно переслано в '{entity.title}'"
                + (f" (топик {topic_id})" if topic_id else "")
            )
            await asyncio.sleep(
                self.randomized_utils.get_randomized_delay(FORWARD_DELAY, 5)
            )
        except UserBannedInChannelError:
            print(f"[!] Аккаунт забанен в {entity.title}. Пропускаю.")
            return
        except ChatWriteForbiddenError:
            print(f"[!] Нет доступа к {entity.title}, пропускаю.")
            return
        except Exception as e:
            await self.error_handler_service._handle_forward_error(e, phone, entity)

    async def _reset_queue(self, csv_path: str):
        """Сбрасывает очередь и обновляет CSV флаги"""
        try:
            # Сбрасываем флаги в CSV
            self.csv_repo.reset_message_sent_flag(csv_path)

            # Перезаполняем очередь
            self.shared_queue = asyncio.Queue()
            chat_data = self.csv_repo.read_chat_data(csv_path)

            # Добавляем все сообщения
            for chat in chat_data:
                await self.shared_queue.put(chat)

        except Exception as e:
            print(f"[!] Ошибка сброса очереди: {str(e)}")

    # async def _handle_peer_flood_error(self, phone: str, e: Exception, filename: str):
    # print(f"[!] Получил спамблок от Telegram | {phone}: {e.message}")
    # return await self._replace_banned_account(phone, STATUS_SPAM_BLOCK)

    async def _replace_banned_account(self, phone: str, status: str):
        await self._safe_disconnect_account(phone, status, True)
        new_accs = self.account_repo.get_free_accounts()
        if new_accs:
            new_phone = new_accs[0].phone
            client = await self.client_service.authenticate_and_set_status(new_phone)
            if client:
                self.active_accounts[new_phone] = client
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
                print(
                    "[!] Все аккаунты в долгом ожидании или заблокированы. Завершение работы..."
                )
                await self._safe_disconnect_all_accs(status)
                sys.exit(0)

        return None

    # async def _handle_peer_flood_error(self, phone: str):
    #     del self.active_accounts[phone]
    #     await self._safe_disconnect_account(phone, STATUS_SPAM_BLOCK, True)

    #     # Проверяем остались ли активные аккаунты
    #     if not self.active_accounts:
    #         free_accounts = self.account_repo.get_free_accounts()
    #         if not free_accounts:
    #             await self._safe_disconnect_all_accs(STATUS_SPAM_BLOCK)
    #             print("[!] Все аккаунты заблокированы. Программа завершается")
    #             await asyncio.sleep(1)
    #             sys.exit(1)

    #     phone_new_account = await self._replace_banned_account()
    #     if phone_new_account:
    #         print(f"[+] Взял в работу новый аккаунт {phone_new_account}")
    #     else:
    #         print(
    #             f"[!] Свободные аккаунты закончились. Активных: {len(self.active_accounts)}"
    #         )
    #         if not self.active_accounts:
    #             await self._safe_disconnect_all_accs(STATUS_SPAM_BLOCK)
    #             print("[!] Нет рабочих аккаунтов. Программа завершается")
    #             await asyncio.sleep(1)
    #             sys.exit(1)

    # async def _replace_banned_account(self):
    #     new_account = self.account_repo.get_free_accounts()
    #     if new_account:
    #         client = await self.client_service.authenticate_and_set_status(
    #             new_account[0].phone
    #         )
    #         if client:
    #             self.active_accounts[new_account[0].phone] = client
    #             # self.account_repo.update_status_by_phone(
    #             #     new_account[0].phone, STATUS_IN_WORK
    #             # )
    #             return new_account[0].phone
    #     else:
    #         return None

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
            # Асинхронное отключение
            await client.disconnect()

            # Обновление статуса если указано
            if status is not None:
                self.account_repo.update_status_by_phone(phone, status)

            # Удаление из активных аккаунтов
            if remove_from_active:
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
