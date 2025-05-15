from core.dependencies import Dependencies
from core.use_cases.pars_chat_list_uc import ParsChatListUseCase
from interfaces.cli.handlers.account_selection_handler import handle_account_selection


async def handle_pars_chat_list(container: Dependencies):
    selected_account = handle_account_selection(container)
    if not selected_account:
        return
    
    filename = input("[+] Введите имя файла для сохранения: ")

    pars_chat_list_uc = container.pars_chat_list_uc
    number_of_found_groups = await pars_chat_list_uc.search_global_groups(
        selected_account.phone, filename
    )
    if number_of_found_groups:
        print(f"\n🔍 Всего найдено групп: {number_of_found_groups}")
    else:
        print(f"\n🚨 Не удалось спарсить группы!")
