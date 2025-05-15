from core.dependencies import Dependencies
from interfaces.cli.handlers.mass_account_selection_handler import (
    handle_mass_account_selection,
)


async def handle_mass_pars_channel_list(container: Dependencies):

    num_accounts = handle_mass_account_selection(container)
    if not num_accounts:
        return

    filename = input("[+] Введите название файла: ").strip().lower()

    mass_pars_channel_list_uc = container.mass_pars_channel_list_uc
    time_str, parsing_status, number_of_found_channels = (
        await mass_pars_channel_list_uc.run(num_accounts, filename)
    )
    if number_of_found_channels:
        print(f"\n✅ Парсинг списка каналов завершен со статусом '{parsing_status}'")
        print(f"⏱ Общее время выполнения: {time_str}")
        print(f"📊 Найдено каналов: {number_of_found_channels}")
    else:
        print(f"\n🚨 Не удалось спарсить каналы!")
