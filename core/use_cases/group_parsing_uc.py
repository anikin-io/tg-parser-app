import time
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, ChannelParticipantsSearch
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest

class GroupParsingUseCase:
    def __init__(self, client):
        self.client = client

    async def get_groups(self):
        chats = []
        groups = []
        result = await self.client(GetDialogsRequest(
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
            except Exception:
                continue
        return groups

    async def parse_group(self, group_index: int):
        groups = await self.get_groups()
        if not groups:
            raise ValueError("Нет доступных групп для парсинга")
        if group_index < 0 or group_index >= len(groups):
            raise ValueError("Неверный номер группы")
        target_group = groups[group_index]
        full = await self.client(GetFullChannelRequest(target_group))
        participant_count = full.full_chat.participants_count
        print(f"В группе {participant_count} пользователей.")
        start_time = time.time()
        all_participants = []
        if participant_count > 10000:
            print('[+] Обработка большой группы...')
            alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
            next_char = 'a'
            limit = 200
            unique_ids = set()
            while next_char:
                offset = 0
                print(f"Ищу участников с логинами, начинающимися на '{next_char}'...")
                while True:
                    participants = await self.client(GetParticipantsRequest(
                        channel=target_group,
                        filter=ChannelParticipantsSearch(next_char),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))
                    if not participants.users:
                        break
                    for user in participants.users:
                        if user.id not in unique_ids:
                            unique_ids.add(user.id)
                            all_participants.append(user)
                    offset += limit
                next_index = alphabet.index(next_char) + 1
                next_char = alphabet[next_index] if next_index < len(alphabet) else None
        else:
            print('[+] Обработка маленькой группы...')
            all_participants = await self.client.get_participants(target_group, aggressive=True)
        end_time = time.time()
        elapsed_time = end_time - start_time
        return {
            "target_group": target_group,
            "participants": all_participants,
            "participant_count": participant_count,
            "elapsed_time": elapsed_time
        }
