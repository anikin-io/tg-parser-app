import asyncio
from interfaces.cli.handlers.auth_handler import handle_account_authorization


def main_menu():
    while True:
        print("\n--- Главное меню ---")
        print(
            "1. Подготовить аккаунт - тест (выбор, проверка session, конвертация, авторизация)"
        )
        print("2. Выход")
        choice = input("[+] Выберите действие: ")

        if choice == "1":
            asyncio.run(handle_account_authorization())
        elif choice == "2":
            print("Выход из приложения...")
            break
        else:
            print("[!] Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main_menu()
