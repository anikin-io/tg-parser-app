import asyncio
from typing import Optional

from telethon import functions
from telethon.errors import (
    ChatWriteForbiddenError,
    UserBannedInChannelError,
    UserNotParticipantError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat, User

from config.constants import FORWARD_DELAY, JOIN_DELAY, LOOP_INTERVAL, MAX_CHATS_LIMIT


class ForwardingUseCase:
    def __init__(
        self,
        client_service,
        account_repo,
        csv_repo,
        message_utils,
        randomized_utils,
        tg_urls_utils,
        error_handler_service,
    ):
        # self.auth_use_case = AuthUseCase()
        # self.account_repo = AccountRepository()

        self.client_service = client_service
        self.account_repo = account_repo
        self.csv_repo = csv_repo
        self.message_utils = message_utils
        self.randomized_utils = randomized_utils
        self.tg_urls_utils = tg_urls_utils
        self.error_handler_service = error_handler_service
        self.me_cache = {}  # Кэш для хранения me по номеру телефона

    # TODO: сменить на обычный метод
    def get_list_csv_files(self):
        return self.csv_repo.list_csv_files()

    # Главная функция
    async def forward_post(
        self,
        phone: str,
        join_groups: bool,
        choice_csv_file: Optional[int],
        csv_files: list,
    ):
        client = await self._authenticate_and_prepare(phone)
        if not client:
            return

        chat_list = await self._prepare_target_chats(
            client, phone, join_groups, choice_csv_file, csv_files
        )
        if not chat_list:
            await client.disconnect()
            return

        source_chat, message_id = await self._select_source_content(client)
        if not source_chat or not message_id:
            await client.disconnect()
            return

        await self._process_forwarding(
            client, phone, chat_list, source_chat, message_id
        )
        # await self._safe_disconnect(client, phone)
        await self.client_service.safe_disconnect(client, phone)

    # Основные подфункции
    # async def _authenticate_and_prepare(self, phone: str):
    #     """Аутентификация и подготовка клиента"""
    #     client = await self.auth_use_case.authenticate(phone)
    #     if client:
    #         me_user = await client.get_me()
    #         self.me_cache[phone] = me_user
    #         self.account_repo.update_status_by_phone(phone, STATUS_IN_WORK)
    #         return client
    #     print(f"[!] Не удалось авторизовать аккаунт {phone}")
    #     return None
    async def _authenticate_and_prepare(self, phone: str):
        """Аутентификация и подготовка клиента"""
        client = await self.client_service.authenticate_and_set_status(phone)
        if client:
            me_user = await client.get_me()
            self.me_cache[phone] = me_user
            return client
        print(f"[!] Не удалось авторизовать аккаунт {phone}")
        return None

    async def _prepare_target_chats(
        self, client, phone, join_groups, choice_csv_file, csv_files
    ):
        """Подготовка списка целевых чатов"""
        if join_groups:
            return await self._join_groups_from_csv(
                client, phone, choice_csv_file, csv_files
            )
        return await self._get_existing_groups(client, phone)

    async def _join_groups_from_csv(self, client, phone, choice_csv_file, csv_files):
        """Вступление в группы из CSV"""
        chat_list = []
        csv_file = self.csv_repo.choice_csv_file(choice_csv_file, csv_files)
        chat_urls = self.csv_repo.read_chat_urls(csv_file)

        current_dialogs = await client.get_dialogs()
        current_chat_ids = {d.entity.id for d in current_dialogs}
        current_count = len(
            [d for d in current_dialogs if isinstance(d.entity, (Channel, Chat))]
        )
        print(
            f"[+] Текущее количество чатов/каналов: {current_count}/{MAX_CHATS_LIMIT}"
        )

        print(f"[+] Попытка вступить в {len(chat_urls)} чатов из базы...")
        for chat_url in chat_urls:
            if current_count >= MAX_CHATS_LIMIT:
                print("[!] Достигнут лимит чатов/каналов. Прекращаю вступление.")
                break
            entity, topic_id = await self._process_single_chat(
                client, phone, chat_url, current_chat_ids
            )
            if entity:
                chat_list.append({"entity": entity, "topic": topic_id})
                current_count += 1
            await asyncio.sleep(
                self.randomized_utils.get_randomized_delay(JOIN_DELAY, 5)
            )
        return chat_list


    async def _process_single_chat(self, client, phone, chat_url, current_chat_ids):
        """Вступление в один чат с последующей проверкой прав"""
        base_url, topic_id = self.tg_urls_utils.parse_chat_link(chat_url)
        try:
            entity = await client.get_entity(base_url)

            if entity.id in current_chat_ids:
                print(f"[✓] Уже состоите в '{entity.title}', иду дальше | {phone}")
                return entity, topic_id

            await client(JoinChannelRequest(entity))
            print(
                f"[✓] Вступили в '{entity.title}'"
                + (f" (топик {topic_id}) | {phone}" if topic_id else f" | {phone}")
            )
            return entity, topic_id

        except Exception as e:
            if "requested to join" in str(e):
                print(
                    f"[~] Заявка в '{entity.title}' отправлена, берем в работу | {phone}"
                )
                return entity, topic_id
            else:
                await self.error_handler_service._handle_join_errors(e, phone, chat_url)
        return None, None

    async def _get_existing_groups(self, client, phone):
        """Получение существующих групп"""
        try:
            dialogs = await client.get_dialogs()
            return [
                {"entity": d.entity, "topic": None}
                for d in dialogs
                if isinstance(d.entity, Channel) and d.entity.megagroup
            ]
        except Exception as e:
            await self.error_handler_service._handle_group_fetch_error(e, phone)

    async def _select_source_content(self, client):
        """Выбор исходного контента"""
        await self._print_dialogs_list(client)
        selected_id = input("[+] Введите ID чата/канала для выбора поста: ")
        if not selected_id.isdigit():
            print("[!] Некорректный ID.")
            return None, None

        messages = await client.get_messages(int(selected_id), limit=50)
        if not messages:
            print("[!] Нет сообщений в выбранном чате/канале.")
            return None, None

        await self._print_messages_list(messages)
        msg_id = input("[+] Введите ID сообщения для пересылки: ")
        return int(selected_id), int(msg_id) if msg_id.isdigit() else None

    async def _print_dialogs_list(self, client):
        """Вывод списка всех диалогов"""
        dialogs = await client.get_dialogs()
        print("[+] Список всех диалогов аккаунта:")
        for d in dialogs:
            entity = d.entity
            if isinstance(entity, Channel):
                if entity.megagroup:
                    print(f"Чат ID: {entity.id}, Название: {entity.title}")
                else:
                    print(f"Канал ID: {entity.id}, Название: {entity.title}")
            elif isinstance(entity, User):
                if entity.bot:
                    bot_name = entity.first_name or entity.username or "Unknown Bot"
                    print(f"Бот ID: {entity.id}, Имя: {bot_name}")
                else:
                    user_name = entity.first_name or "Unknown User"
                    print(f"Юзер ID: {entity.id}, Имя: {user_name}")
            else:
                print(
                    f"Неизвестный ID: {entity.id}, Тип: {type(entity).__name__ or "Unknown Type"}"
                )

    async def _print_messages_list(self, messages):
        """Вывод списка сообщений"""
        print("[+] Сообщения в выбранном чате/канале:")
        for msg in messages:
            preview = (msg.message or "None")[:50]
            print(f"ID: {msg.id}, Превью: {preview}")

    async def _process_forwarding(
        self, client, phone, chat_list, source_chat, message_id
    ):
        """Основной процесс пересылки нескольких сообщений"""
        print(f"[+] Сообщение будет переслано в {len(chat_list)} чатов.")
        while True:
            for dest in chat_list:
                channel = dest["entity"]
                topic_id = dest["topic"]

                success = await self._forward_single_message(
                    client, phone, source_chat, message_id, channel, topic_id
                )
                if not success:
                    continue

            if LOOP_INTERVAL < 0:
                break
            else:
                await self._handle_loop_delay()

    async def _forward_single_message(
        self, client, phone, source_chat, message_id, channel, topic_id
    ):
        """Пересылка сообщения в один чат с обработкой ошибок и проверками"""
        # channel = dest["entity"]
        # topic_id = dest["topic"]

        if not await self._check_chat_permissions(client, channel, phone):
            # print(f"[!] Не прошел проверку прав {channel.title} , пропускаем | {phone}")
            return False

        try:
            me = self.me_cache.get(phone)
            my_id = me.id
            last_msg = await client.get_messages(channel, limit=1)
            if last_msg and last_msg[0].sender_id == my_id:
                if not self.message_utils.is_system_message(last_msg[0]):
                    print(
                        f"[!] Последнее сообщение в {channel.title} наше, пропускаю | {phone}"
                    )
                    return False
        except Exception as e:
            print(f"[!] Ошибка проверки сообщений в {channel.title}: {e} | {phone}")

        try:
            if topic_id:
                await client(
                    functions.messages.ForwardMessagesRequest(
                        from_peer=source_chat,
                        id=[message_id],
                        to_peer=channel,
                        top_msg_id=topic_id,
                    )
                )
            else:
                await client.forward_messages(
                    channel, message_id, from_peer=source_chat
                )

            print(
                f"[✓] Успешно переслано в '{channel.title}'"
                + (f" (топик {topic_id}) | {phone}" if topic_id else f" | {phone}")
            )
            await asyncio.sleep(
                self.randomized_utils.get_randomized_delay(FORWARD_DELAY, 5)
            )
            return True
        except UserBannedInChannelError:
            print(f"[!] Аккаунт забанен в {channel.title}. Пропускаю. | {phone}")
            return False
        except ChatWriteForbiddenError:
            print(f"[!] Нет доступа к {channel.title}, пропускаю. | {phone}")
            return False
        except Exception as e:
            await self.error_handler_service._handle_forward_error(e, phone, channel)
            return False

    # def _is_system_message(self, message: Message) -> bool:
    #     """Проверяет, является ли сообщение системным"""
    #     # 1. Проверка типа сообщения
    #     if isinstance(message, MessageService):
    #         return True

    #     # 2. Проверка системных отправителей
    #     if message.from_id:
    #         system_ids = {
    #             777000,  # Telegram Notifications
    #             1087968824,  # GroupAnonymousBot
    #         }
    #         if isinstance(message.from_id, PeerUser):
    #             if message.from_id.user_id in system_ids:
    #                 return True

    #     # 3. Анализ текста сообщения
    #     if message.message:
    #         system_patterns = [
    #             r"(?i)(теперь (в группе|участник))",
    #             r"(?i)(joined (the|this) (group|channel))",
    #             r"(?i)(добавлен|присоединился)",
    #             r"(?i)(created (group|channel))",
    #         ]
    #         text = message.message.lower()
    #         if any(re.search(p, text) for p in system_patterns):
    #             return True

    #     # 4. Проверка пустого контента
    #     if not message.message and not message.media:
    #         return True

    #     return False

    async def _check_chat_permissions(self, client, channel, phone):
        """Проверка прав в канале"""
        try:
            me = self.me_cache.get(phone)
            try:
                permissions = await client.get_permissions(channel, me)
            except UserNotParticipantError:
                print(f"[!] Заявка не одобрена в {channel.title} | {phone}")
                return False
            except Exception as e:
                print(
                    f"[!] Ошибка проверки участия в {channel.title}: {str(e)} | {phone}"
                )
                return False

            if not permissions:
                print(
                    f"[!] Не прошел проверку прав {channel.title} , пропускаю | {phone}"
                )
                return False
            else:
                if permissions.is_banned:
                    print(f"[!] Пользователь забанен в {channel.title} | {phone}")
                    return False
                if permissions.has_left:
                    print(f"[!] Пользователь покинул {channel.title} | {phone}")
                    return False
                if permissions.has_default_permissions:
                    print(f"[✓] Успешная проверка базовых прав | {phone}")
                    return True

                if channel.default_banned_rights.send_messages:
                    print(f"[!] Нет прав на отправку в {channel.title} | {phone}")
                    return False
                # if isinstance(channel, Channel) and channel.join_request:
                #     print(f"[~] Ожидается одобрение заявки в {channel.title} | {phone}")
                #     return False
                # if channel.join_to_send:
                #     return await self._join_channel(client, channel)
                return True

        except ChatWriteForbiddenError:
            print(f"[!] Нет прав доступа к чату: {str(e)} | {phone}")
            return False
        except Exception as e:
            print(f"[!] Общая ошибка проверки прав: {str(e)} | {phone}")
            return False

    async def _join_channel(self, client, channel):
        """Вступление в канал"""
        try:
            await client(JoinChannelRequest(channel))
            await asyncio.sleep(
                self.randomized_utils.get_randomized_delay(JOIN_DELAY, 5)
            )
            return True
        except Exception as e:
            print(f"[!] Не удалось вступить в {channel.title}: {str(e)}")
            return False

    # async def _handle_group_fetch_error(self, error: Exception, phone: str):
    #     """Обработчик ошибок при получении списка групп"""
    #     if isinstance(error, FloodWaitError):
    #         print(f"[!] Лимит запросов. Жду {error.seconds} сек. | {phone}")
    #         await asyncio.sleep(error.seconds)
    #     elif isinstance(error, PeerFloodError):
    #         print(f"[!] Получил спамблок от Telegram | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         raise CustomPeerFloodError(phone, error) from error
    #     else:
    #         print(f"[!] Неизвестная ошибка: {str(error)} | {phone}")

    # async def _handle_forward_error(self, error, phone, channel):
    #     """Обработка ошибок пересылки"""
    #     if isinstance(error, FloodWaitError):
    #         print(f"[!] Лимит запросов. Жду {error.seconds} сек | {phone}")
    #         await asyncio.sleep(error.seconds)
    #     elif isinstance(error, PeerFloodError):
    #         print(f"[!] Получил спамблок от Telegram | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         raise CustomPeerFloodError(phone, error) from error
    #     elif "spam" in str(error).lower():
    #         print(f"[!] Получил спамблок от Telegram | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         raise CustomPeerFloodError(phone, error) from error
    #     elif "Cannot send requests while disconnected" in str(error):
    #         print(f"[!] Выкинуло из аккаунта, возможно получил бан | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         raise CustomPeerFloodError(phone, error) from error
    #     else:
    #         print(f"[!] Ошибка при пересылке в {channel.title}: {error} | {phone}")

    # async def _handle_join_errors(self, error, phone, chat_url):
    #     """Обработка ошибок вступления"""
    #     if isinstance(error, ChannelPrivateError):
    #         print(f"[!] Чат/канал {chat_url} приватный | {phone}")
    #     elif isinstance(error, ChannelInvalidError):
    #         print(f"[!] Чат/канал {chat_url} не существует или недоступен | {phone}")
    #     elif isinstance(error, FloodWaitError):
    #         print(
    #             f"[!] Лимит запросов к Telegram исчерпан. Жду {error.seconds} сек | {phone}"
    #         )
    #         await asyncio.sleep(error.seconds)
    #     elif isinstance(error, PeerFloodError):
    #         print(f"[!] Получил спамблок от Telegram | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         # Пробрасываем кастомное исключение
    #         raise CustomPeerFloodError(phone, error) from error
    #     elif "Cannot send requests while disconnected" in str(error):
    #         print(f"[!] Выкинуло из аккаунта, возможно получил бан | {phone}")
    #         self.account_repo.update_status_by_phone(phone, STATUS_SPAM_BLOCK)
    #         raise CustomPeerFloodError(phone, error) from error
    #     else:
    #         print(f"[!] Неизвестная ошибка: {str(error)} | {phone}")

    async def _handle_loop_delay(self):
        """Обработка задержки между циклами"""
        print(f"[+] Ожидание примерно {LOOP_INTERVAL} секунд между циклами...")
        await asyncio.sleep(
            self.randomized_utils.get_randomized_delay(LOOP_INTERVAL, 10)
        )

    # async def _safe_disconnect(self, client, phone):
    #     """Безопасное отключение тг-клиента"""
    #     await client.disconnect()
    #     self.account_repo.update_status_by_phone(phone, STATUS_FREE)
