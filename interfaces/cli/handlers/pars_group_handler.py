import asyncio

from core.dependencies import Dependencies
from infrastructure.repositories.csv_repo import CSVRepository
from interfaces.cli.handlers.account_selection_handler import handle_account_selection
from interfaces.controllers.pars_group_controller import ParsGroupController


async def handle_group_parsing(container: Dependencies):

    selected_account = handle_account_selection(container)

    gc = ParsGroupController()
    # Получаем список групп для выбранного аккаунта
    groups, client = await gc.get_groups_for_account(selected_account.phone)
    if groups is None or client is None:
        print("[!] Не удалось получить список групп.")
        return

    print("[+] Доступные группы для парсинга:")
    for i, g in enumerate(groups):
        print(f"[{i}] - {g.title}")

    group_index_input = input("[+] Введите номер группы: ")
    try:
        group_index = int(group_index_input)
    except ValueError:
        print("[!] Некорректный ввод номера группы.")
        await client.disconnect()
        return

    result = await gc.parse_group_for_account(
        selected_account.phone, group_index, client
    )
    if result is None:
        print("[!] Парсинг не выполнен.")
        await client.disconnect()
        return

    target_group = result["target_group"]
    participants = result["participants"]
    participant_count = result["participant_count"]
    elapsed_time = result["elapsed_time"]
    percentage = (
        (len(participants) / participant_count) * 100 if participant_count > 0 else 0
    )

    print(f"[+] Найдено участников: {len(participants)} из {participant_count}")
    csv_filename = input("[+] Введите название файла для сохранения результатов: ")
    csv_path = CSVRepository.save_participants(csv_filename, participants, target_group)
    print(f"[+] Участники сохранены в {csv_path}")
    print(f"[+] Найдено участников: {len(participants)} из {participant_count}")
    print(f"[+] Процент полученных участников: {percentage:.2f}%")

    if elapsed_time >= 60:
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        time_output = f"{int(minutes)} минут(ы) {int(seconds)} секунд(ы)"
    else:
        time_output = f"{int(elapsed_time)} секунд(ы)"
    print(f"[+] Время парсинга: {time_output}")
    await client.disconnect()
