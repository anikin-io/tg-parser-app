from infrastructure.database.db_config import init_db
from interfaces.cli.menus.main_menu import main_menu


def main():
    # Инициализация базы данных (создание таблиц, если их нет)
    # init_db()
    main_menu()


if __name__ == "__main__":
    main()
