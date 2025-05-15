import asyncio

from core.dependencies import Dependencies
from interfaces.cli.handlers.ai_commenting_handler import handle_ai_commenting
from interfaces.cli.handlers.forward_handler import handle_forward_post
from interfaces.cli.handlers.mass_forward_handler import handle_mass_forward
from interfaces.cli.handlers.mass_pars_channel_list_handler import (
    handle_mass_pars_channel_list,
)
from interfaces.cli.handlers.mass_pars_chat_list_handler import (
    handle_mass_pars_chat_list,
)
from interfaces.cli.handlers.pars_chat_list_handler import handle_pars_chat_list
from interfaces.cli.handlers.pars_group_handler import handle_group_parsing


def main_menu(container: Dependencies):
    while True:
        print("\n--- Главное меню ---")
        print("1. Парсинг участников группы")
        print("2. Пересылка поста по базе чатов")
        print("3. Массовая пересылка поста по базе чатов")
        print("4. Глобальный парсинг чатов по ключевым словам")
        print("5. Глобальный парсинг чатов по ключевым словам с разных аккаунтов")
        print("6. Нейрокомментинг по базе каналов")
        print("7. Глобальный парсинг каналов по ключевым словам с разных аккаунтов")
        print("8. Выход")
        choice = input("[+] Выберите действие: ")

        if choice == "1":
            asyncio.run(handle_group_parsing(container))
        elif choice == "2":
            asyncio.run(handle_forward_post(container))
        elif choice == "3":
            asyncio.run(handle_mass_forward(container))
        elif choice == "4":
            asyncio.run(handle_pars_chat_list(container))
        elif choice == "5":
            asyncio.run(handle_mass_pars_chat_list(container))
        elif choice == "6":
            asyncio.run(handle_ai_commenting(container))
        elif choice == "7":
            asyncio.run(handle_mass_pars_channel_list(container))
        elif choice == "8":
            print("Выход из приложения...")
            break
        else:
            print("[!] Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main_menu()
