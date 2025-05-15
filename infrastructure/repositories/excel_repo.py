import os
from typing import Dict, List

import pandas as pd


class ExcelRepository:

    @staticmethod
    def save_groups_to_excel(groups_data: List[Dict], filename: str) -> None:
        """
        Сохраняет данные о группах в файл Excel (XLSX)
        с автоматическим форматированием колонок

        :param groups_data: Список словарей с данными о группах
        :param filename: Имя файла без расширения
        """
        if not groups_data:
            print("⚠️ Нет данных для сохранения")
            return

        try:
            # Создаем DataFrame
            df = pd.DataFrame(groups_data)

            # Упорядочиваем колонки (пример, можно настроить под свои нужды)
            column_order = [
                "title",
                "username",
                "about",
                "members",
                "link",
                "id",
            ]

            # Оставляем только существующие колонки
            df = df.reindex(columns=[col for col in column_order if col in df.columns])

            # Создаем папку если нужно
            os.makedirs("excel_reports", exist_ok=True)
            excel_path = os.path.join("excel_reports", f"{filename}_excel.xlsx")

            # Настройки форматирования
            auto_size_exclude = ["about"]
            col_widths = {
                "title": 35,
                "username": 20,
                "members": 15,
                "link": 40,
                "id": 15,
                "about": 80,  # Фиксированная ширина для длинного текста
            }

            # Сохраняем в Excel с авто-шириной колонок
            with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Groups")

                # Настраиваем форматирование
                workbook = writer.book
                worksheet = writer.sheets["Groups"]

                # Формат заголовков
                header_format = workbook.add_format(
                    {
                        "bold": True,
                        "text_wrap": True,
                        "valign": "top",
                        "fg_color": "#D7E4BC",
                        "border": 1,
                    }
                )

                # Настройка ширины колонок
                for idx, col in enumerate(df.columns):
                    # Пропускаем колонки из исключений
                    if col in auto_size_exclude:
                        worksheet.set_column(idx, idx, col_widths.get(col, 50))
                        continue

                    # Авто-ширина для остальных
                    max_len = (
                        max(df[col].astype(str).apply(len).max(), len(str(col))) + 2
                    )
                    worksheet.set_column(idx, idx, max_len)

                # Применяем формат к заголовкам
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            return excel_path

        except Exception as e:
            print(f"[!] Ошибка при сохранении Excel файла: {str(e)}")
            return None
