from core.dependencies import Dependencies


def handle_mass_account_selection(container: Dependencies):

    account_selection_uc = container.account_selection_uc
    free_accounts = account_selection_uc.get_free_accounts()
    free_count = len(free_accounts)

    if free_count == 0:
        print("[!] Нет свободных аккаунтов.")
        return None

    print(f"[+] Доступно свободных аккаунтов: {free_count}")

    try:
        choice = int(input("[+] Введите количество аккаунтов для выбора: "))
    except ValueError:
        print("[!] Некорректный ввод. Требуется числовое значение.")
        return None

    if choice < 1:
        print("[!] Количество не может быть меньше 1.")
        return None

    if choice > free_count:
        print(f"[!] Недостаточно аккаунтов. Максимально доступно: {free_count}")
        return None

    print(f"[+] Успешно выбрано {choice} аккаунтов")
    return choice
