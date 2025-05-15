import asyncio
import itertools
import json
import random

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, ChannelForbidden
from telethon.errors import FloodWaitError


class ParsChatListUseCase:
    def __init__(
        self, client_service, account_repo, message_utils, csv_repo, excel_repo
    ):
        self.client_service = client_service
        self.account_repo = account_repo
        self.message_utils = message_utils
        self.csv_repo = csv_repo
        self.excel_repo = excel_repo

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

    async def search_global_groups(self, phone: str, filename: str):
        # Конфигурация
        base_keywords = ["работа", "подработка", "халтура", "вакансии", "ищу работу", "ищу подработку", "вахта", "шабашка"]
        suffixes = [
            "тула", "брянск", "химки", "сургут", "красногорск", "пенза", "смоленск", "нижневартовск",
            "москва", "мск", "солнечногорск", "тверь", "одинцово", "щербинка", "липецк", "сочи", "калуга",
            "казань", "санкт-петербург", "питер", "спб", "воронеж", "ростов-на-дону", "ростов", "ульяновск",
            "барнаул", "тольятти", "мурманск", "киров", "вятка", "мытищи", "омск", "рязань", 
            "архангельск", "краснодар", "новосибирск", "нск", "новосиб", "нижний новгород", "нижний", "екатеринбург","екб", "московская область", "мо",
            "для мигрантов", "для приезших", "для студентов"
        ]

        exclude_keywords = ["дропы", "казино", "инвестиции", "крипта", "пирамида", "ставки", "закладки", "банки"] # Минус-слова
        min_members = 600
        MAX_TIME_WAITING = 900

        # Генерация уникальных запросов
        queries = list(
            {
                f"{word} {suffix}".strip().lower()
                for word, suffix in itertools.product(base_keywords, suffixes)
            }
        )

        found_groups = {}

        client = await self.client_service.authenticate_and_set_status(phone)
        try:
            for query in queries:
                print(f"🌍 Глобальный поиск: '{query}'")
                result = await client(SearchRequest(q=query, limit=100))

                for chat in result.chats:
                    # Фильтруем только публичные супергруппы
                        if (
                            isinstance(chat, Channel)
                            and chat.megagroup
                            and not isinstance(chat, ChannelForbidden)
                            and chat.username
                        ):

                            # Проверка на дубликаты и права
                            if (
                                (chat.id in found_groups)
                                or chat.default_banned_rights.send_messages
                                or chat.join_request
                            ):
                                continue

                            try:
                                full_chat = await client.get_entity(chat.username)

                                if any(kw in full_chat.title.lower() for kw in exclude_keywords):
                                    continue

                                chat_full_info = await client(
                                    GetFullChannelRequest(channel=full_chat)
                                )
                                if (
                                    chat_full_info.full_chat.participants_count
                                    <= min_members
                                ):
                                    continue

                                # Проверка на минус-слова в названии и описании
                                title_lower = full_chat.title.lower()
                                about_lower = (
                                    chat_full_info.full_chat.about.lower() or "None"
                                )
                                # if any(
                                #     keyword in title_lower or keyword in about_lower
                                #     for keyword in exclude_keywords
                                # ):
                                #     print(
                                #         f"🚫 Чат {full_chat.title} отфильтрован по минус-слову"
                                #     )
                                #     continue

                                # Ищем первое совпавшее минус-слово
                                excluded_keyword = None
                                for keyword in exclude_keywords:
                                    if keyword in title_lower or keyword in about_lower:
                                        excluded_keyword = keyword
                                        break  # Прерываем цикл после первого найденного слова
                                if excluded_keyword is not None:
                                    print(f"🚫 Чат {full_chat.title} отфильтрован по минус-слову: {excluded_keyword}")
                                    continue

                                # if not await self.check_chat_activity(
                                #     client, full_chat, 30, 10
                                # ):
                                #     print(
                                #         f"🚫 Чат {full_chat.title} не имеет необходимого числа пользовательского контента"
                                #     )
                                #     continue
                            except FloodWaitError as e:
                                if e.seconds > MAX_TIME_WAITING:
                                    raise
                                else:
                                    print(f"⏳ Нужно подождать {e.seconds} сек...")
                                    await asyncio.sleep(e.seconds)
                                    continue
                            except Exception as e:
                                print(f"⚠️ Ошибка доступа к {chat.username}: {str(e)}")
                                continue

                            found_groups[full_chat.id] = {
                                "title": full_chat.title,
                                "username": full_chat.username,
                                "members": chat_full_info.full_chat.participants_count,
                                "link": f"https://t.me/{full_chat.username}",
                                "id": full_chat.id,
                                "about": chat_full_info.full_chat.about or "——",
                            }
                            print(
                                f"✅ Найдена: {full_chat.title} ({chat_full_info.full_chat.participants_count} участника(-ов))"
                            )
                        await asyncio.sleep(random.uniform(1, 2))

                await asyncio.sleep(random.uniform(10, 20))

        except FloodWaitError as e:
                if e.seconds > MAX_TIME_WAITING:
                    print("🚦 Обнаружено долгое ожидание {e.seconds} сек.! Сохраняем результаты...")
                    if found_groups:
                        self.csv_repo.save_groups_to_csv(list(found_groups.values()), filename)
                        self.excel_repo.save_groups_to_excel(list(found_groups.values()), filename)
                    
                    await self.client_service.safe_disconnect_with_pause(client, phone)
                    return len(found_groups) 
        except Exception as e:
                print(f"🚨 Критическая ошибка: {str(e)}")
                return None
        finally:
            if found_groups:
                self.csv_repo.save_groups_to_csv(list(found_groups.values()), filename)
                self.excel_repo.save_groups_to_excel(list(found_groups.values()), filename)
        
        await self.client_service.safe_disconnect(client, phone)
        return len(found_groups)
