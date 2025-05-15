from core.dependencies import Dependencies


def handle_account_selection(container: Dependencies):

    account_selection_uc = container.account_selection_uc
    free_accounts = account_selection_uc.get_free_accounts()
    if not free_accounts:
        print("[!] Нет свободных аккаунтов.")
        return

    print("[+] Доступные свободные аккаунты:")
    for idx, acc in enumerate(free_accounts, start=1):
        print(f"{idx}. {acc.phone} ({acc.name})")
    choice = input("[+] Выберите номер аккаунта: ")
    try:
        choice = int(choice)
    except ValueError:
        print("[!] Некорректный ввод.")
        return
    if choice < 1 or choice > len(free_accounts):
        print("[!] Неверный номер аккаунта.")
        return
    selected_account = free_accounts[choice - 1]
    print(f"[+] Выбран аккаунт: {selected_account.phone}")
    return selected_account
