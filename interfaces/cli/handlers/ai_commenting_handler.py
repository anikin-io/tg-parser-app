from core.dependencies import Dependencies
from interfaces.cli.handlers.mass_account_selection_handler import (
    handle_mass_account_selection,
)


async def handle_ai_commenting(container: Dependencies):

    num_accounts = handle_mass_account_selection(container)
    if not num_accounts:
        return

    print("[+] Нейрокомментинг стартует...")

    ai_commenting_uc = container.ai_commenting_uc
    await ai_commenting_uc.run(num_accounts)

    # if number_of_found_groups:
    #     print(f"\n✅ Парсинг списка групп завершен")
    #     print(f"⏱ Общее время выполнения: {time_str}")
    #     print(f"📊 Найдено групп: {number_of_found_groups}")
    # else:
    #     print(f"\n🚨 Не удалось спарсить группы!")