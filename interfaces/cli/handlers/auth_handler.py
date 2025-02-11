import asyncio
from interfaces.controllers.auth_controller import AuthController


async def handle_account_authorization():
    controller = AuthController()
    free_accounts = controller.get_free_accounts()

    if not free_accounts:
        print("[!] Нет свободных аккаунтов.")
        return

    print("[+] Доступные свободные аккаунты:")
    for idx, account in enumerate(free_accounts, start=1):
        print(f"{idx}. {account.phone} ({account.name})")

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

    proxy = {
        "proxy_type": "socks5",
        "addr": selected_account.proxy_ip,
        "port": int(selected_account.proxy_port),
        "username": selected_account.proxy_username,
        "password": selected_account.proxy_password,
        "rdns": True,
    }
    client = await controller.authenticate_account(selected_account.phone, proxy)

    if client:
        print(
            f"[+] Аккаунт {selected_account.phone} успешно подготовлен и авторизован."
        )
        await client.send_message("me", "Тест: авторизация через session успешна!")
        await client.disconnect()
    else:
        print("[!] Подготовка аккаунта завершилась ошибкой.")
