from core.dependencies import Dependencies
from interfaces.cli.handlers.mass_account_selection_handler import (
    handle_mass_account_selection,
)


async def handle_mass_pars_chat_list(container: Dependencies):

    num_accounts = handle_mass_account_selection(container)
    if not num_accounts:
        return

    filename = input("[+] Введите название файла: ").strip().lower()

    mass_pars_chat_list_uc = container.mass_pars_chat_list_uc
    await mass_pars_chat_list_uc.initialize(num_accounts)
    time_str, parsing_status, number_of_found_groups = (
        await mass_pars_chat_list_uc.start_parsing(filename)
    )
    if number_of_found_groups:
        print(f"\n✅ Парсинг списка групп завершен со статусом '{parsing_status}'")
        print(f"⏱ Общее время выполнения: {time_str}")
        print(f"📊 Найдено групп: {number_of_found_groups}")
    else:
        print(f"\n🚨 Не удалось спарсить группы!")
