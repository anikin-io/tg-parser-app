from core.dependencies import Dependencies
from interfaces.cli.handlers.mass_account_selection_handler import (
    handle_mass_account_selection,
)


async def handle_mass_forward(container: Dependencies):

    num_accounts = handle_mass_account_selection(container)
    if not num_accounts:
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

        while True:
            choice_csv_file = input("[+] Выберите номер CSV файла(0 для отмены): ")

            if choice_csv_file == "0":
                print("[!] Отмена")
                return

            try:
                if int(choice_csv_file) < 1 or int(choice_csv_file) > len(csv_files):
                    print("[!] Неверный выбор.")
                    continue
                if choice_csv_file.isdigit():
                    choice_csv_file = int(choice_csv_file)
                    break
                else:
                    print("[!] Введено не число.")
                    continue
            except ValueError:
                print("[!] Некорректный ввод.")
                continue

    subscribe_channel_choice = (
        input("[+] Подписаться на канал? (Y/N): ").strip().lower()
    )
    subscribe_channel = True if subscribe_channel_choice == "y" else False
    channel_url = None

    if subscribe_channel:
        while True:
            channel_url = input(
                "[+] Введите URL канала для подписки (0 для отмены): "
            ).strip()

            if channel_url == "0":
                print("[!] Отмена")
                return

            # Нормализация URL
            if channel_url.startswith("@"):
                channel_url = f"https://t.me/{channel_url[1:]}"

            if not channel_url.startswith(("http://", "https://")):
                channel_url = f"https://{channel_url}"

            # Проверка валидности
            if container.tg_urls_utils.validate_telegram_url(channel_url):
                break

            print("[!] Некорректный URL. Примеры допустимых форматов:")
            print(" • https://t.me/channel_name")
            print(" • @channel_name")
            print(" • t.me/channel_name")

    while True:
        source_channel_url = input(
            "Введите URL исходного канала (0 для отмены): "
        ).strip()

        if source_channel_url == "0":
            print("[!] Отмена")
            return

        # Нормализация URL
        if source_channel_url.startswith("@"):
            source_channel_url = f"https://t.me/{source_channel_url[1:]}"

        if not source_channel_url.startswith(("http://", "https://")):
            source_channel_url = f"https://{source_channel_url}"

            # Проверка валидности
        if container.tg_urls_utils.validate_telegram_url(source_channel_url):
            break

        print("[!] Некорректный URL. Примеры допустимых форматов:")
        print(" • https://t.me/channel_name")
        print(" • @channel_name")
        print(" • t.me/channel_name")

    while True:
        message_id = input(
            "Введите ID сообщения для пересылки (0 для отмены): "
        ).strip()
        try:
            if message_id == "0":
                print("[!] Отмена")
                return
            if message_id.isdigit():
                message_id = int(message_id)
                break
            else:
                print("[!] Введено не число.")
                continue
        except ValueError:
            print("[!] Некорректный ввод.")
            continue

    mass_forwarding_uc = container.mass_forwarding_uc
    await mass_forwarding_uc.initialize(num_accounts)
    await mass_forwarding_uc.process_mass_forward(
        join_groups=join_groups,
        choice_csv_file=choice_csv_file,
        csv_files=csv_files,
        subscribe_channel=channel_url,
        source_channel_url=source_channel_url,
        message_id=message_id,
    )
