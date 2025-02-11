import os
from modules.database.db_manager import get_free_accounts
from config.statuses import STATUS_FREE

TDATA_FOLDER = "tdata_folder"

def find_available_accounts():
    """Находит аккаунты, которые есть и в БД (со статусом 'свободен'), и в папке tdata_folder."""
    
    # Получаем список телефонов из БД, у которых статус "свободен"
    free_accounts = get_free_accounts()
    free_phones = {account["phone"] for account in free_accounts}  # Преобразуем в set для быстрого поиска
    
    # Получаем список телефонов из папки tdata_folder
    tdata_accounts = {folder for folder in os.listdir(TDATA_FOLDER) if os.path.isdir(os.path.join(TDATA_FOLDER, folder))}
    
    # Найдем совпадающие аккаунты (есть и в БД, и в tdata_folder)
    available_accounts = sorted(free_phones & tdata_accounts)  # Пересечение множеств
    
    return available_accounts

def select_account():
    """Позволяет пользователю выбрать аккаунт из доступных."""
    available_accounts = find_available_accounts()
    
    if not available_accounts:
        print("Нет доступных аккаунтов для выбора.")
        return None
    
    print("\nДоступные аккаунты:")
    for i, phone in enumerate(available_accounts, 1):
        print(f"{i}. {phone}")

    while True:
        try:
            choice = int(input("Введите номер аккаунта для выбора (0 - отмена): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(available_accounts):
                return available_accounts[choice - 1]
            print("Некорректный ввод, попробуйте снова.")
        except ValueError:
            print("Введите число от 1 до", len(available_accounts))

# Тестирование функции при запуске напрямую
if __name__ == "__main__":
    selected = select_account()
    if selected:
        print(f"Выбран аккаунт: {selected}")
