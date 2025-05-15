import asyncio
import re
import sys

from core.dependencies import Dependencies
from core.utils.tg_urls_utils import TelegramUrlsUtils
from infrastructure.database.db_config import init_db
from infrastructure.external.g4f_provider import G4fProvider
from infrastructure.repositories.csv_repo import CSVRepository
from interfaces.cli.menus.main_menu import main_menu


def main():
    # Инициализация базы данных (создание таблиц, если их нет)
    # init_db()
    container = Dependencies()
    main_menu(container)
    # print(TelegramUrlsUtils.get_channel_id_by_url("https://t.me/durov"))


# async def main():
#     phone = "12125554567"
#     lang_code, system_lang = DeviceParamsGenerator.get_phone_number_lang_code(phone)
#     print(f"Lang: {lang_code}, System: {system_lang}")
# await CSVRepository.mark_as_sent(
#     "csv_databases/join_chats_test.csv", "https://t.me/SAMOLET_4_SOSEDI"
# )


if __name__ == "__main__":
    main()

    # Использование
    # ai_provider = G4fProvider()
    # result = asyncio.run(
    #     ai_provider.gpt_request(
    #         "Напиши короткий комментарий в 1-2 предложения без кавычек для поста из телеграм канала на русском языке, ты-хейтер. текст поста: Открыли прямой проход для пешеходов по бульвару Менделеева. И сразу в сети появилось куча вопросов...Что за жертвы ЕГЭ строят дорогу перед метро? Почему на сходах к тротуару сделали пандусы, а не ступеньки? Да ещё и такие крутые, как горка? Представили что там будет зимой после ледяного дождика или снега? Там будет ЛЁД! И люди там будут падать и ломать себе ноги/руки.Где администрация Мурино, которая контролирует работы? Где технадзор? Почему работы никто не контролирует?",
    #         ["gpt-4o-mini", "gpt-4", "gemini-1.5-flash", "deepseek-r1", "gpt-4o",],
    #     )
    # )
    # print(result)
