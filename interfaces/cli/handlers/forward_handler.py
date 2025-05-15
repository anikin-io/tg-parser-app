from core.dependencies import Dependencies
from interfaces.cli.handlers.account_selection_handler import handle_account_selection


async def handle_forward_post(container: Dependencies):
    print("[+] Пересылка поста с канала по базе чатов")

    selected_account = handle_account_selection(container)
    if not selected_account:
        return

    choice_csv_file = None
    csv_files = []

    join_choice = input("[+] Присоединиться к группам? (Y/N): ").strip().lower()
    join_groups = True if join_choice == "y" else False
    forwarding_uc = container.forwarding_uc
    csv_files = forwarding_uc.get_list_csv_files()
    if join_groups:
        if not csv_files:
            print("[!] Нет CSV файлов с базами чатов.")
            return
        print("[+] Доступные CSV базы:")
        for idx, f in enumerate(csv_files, start=1):
            print(f"{idx}. {f}")
        choice_csv_file = input("[+] Выберите номер CSV файла: ")
        try:
            choice_csv_file = int(choice_csv_file)
            if choice_csv_file < 1 or choice_csv_file > len(csv_files):
                print("[!] Неверный выбор.")
                return
        except ValueError:
            print("[!] Некорректный ввод.")
            return

    await forwarding_uc.forward_post(
        phone=selected_account.phone,
        join_groups=join_groups,
        choice_csv_file=choice_csv_file,
        csv_files=csv_files,
    )

