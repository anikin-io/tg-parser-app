import asyncio
import csv
import os
from typing import Dict, List

import portalocker


class CSVRepository:
    @staticmethod
    def save_participants(filename: str, participants, target_group):
        os.makedirs("csv_databases", exist_ok=True)
        csv_path = os.path.join("csv_databases", f"{filename}.csv")
        with open(csv_path, "w", encoding="UTF-8", newline="") as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            writer.writerow(
                [
                    "username",
                    "user_id",
                    "access_hash",
                    "name",
                    "group",
                    "group_username",
                    "message_sent",
                ]
            )
            for user in participants:
                username = user.username or ""
                name = ((user.first_name or "") + " " + (user.last_name or "")).strip()
                if "bot" not in username:
                    writer.writerow(
                        [
                            username,
                            user.id,
                            user.access_hash,
                            name,
                            target_group.title,
                            target_group.username,
                            "False",
                        ]
                    )
        return csv_path

    @staticmethod
    def list_csv_files():
        csv_dir = os.path.join(os.getcwd(), "csv_databases")
        if not os.path.exists(csv_dir):
            return []
        return [f for f in os.listdir(csv_dir) if f.endswith(".csv")]

    @staticmethod
    def choice_csv_file(choice_csv_file: int, csv_files: list[str]):
        csv_file = os.path.join(
            os.getcwd(), "csv_databases", csv_files[choice_csv_file - 1]
        )
        if csv_file:
            return csv_file
        else:
            return None

    # @staticmethod
    # def read_chat_urls(csv_file_path):
    #     chat_urls = []
    #     with open(csv_file_path, "r", encoding="utf-8") as f:
    #         reader = csv.reader(f)
    #         header = next(reader, None)
    #         for row in reader:
    #             # первая колонка содержит URL
    #             if row and row[0].startswith("https://t.me/"):
    #                 chat_urls.append(row[0])
    #     return chat_urls

    @staticmethod
    def read_chat_urls(csv_file_path: str) -> list[str]:
        """Читает только колонку link из CSV файла"""
        return [row["link"] for row in CSVRepository.read_chat_data(csv_file_path)]

    @staticmethod
    def read_chat_data(csv_file_path: str) -> list[dict]:
        """Читает CSV файл с колонками link и message_sent"""
        chat_data = []
        with open(csv_file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Проверяем наличие нужных колонок
            if not {"link", "message_sent"}.issubset(reader.fieldnames):
                raise ValueError(
                    "CSV файл должен содержать колонки: link, message_sent"
                )

            for row in reader:
                # Преобразуем строку в булево значение
                message_sent = row["message_sent"].lower() == "true"

                chat_data.append(
                    {"link": row["link"].strip(), "message_sent": message_sent}
                )
        return chat_data

    @staticmethod
    def reset_message_sent_flag(csv_file_path: str) -> None:
        """
        Сбрасывает все флаги message_sent в False с блокировкой файла
        """
        try:
            with portalocker.Lock(csv_file_path, mode="r+") as f:
                # Читаем все данные
                reader = csv.DictReader(f)
                rows = list(reader)

                # Перемещаемся в начало файла
                f.seek(0)

                # Сбрасываем флаги и записываем обратно
                writer = csv.DictWriter(
                    f, fieldnames=reader.fieldnames, delimiter=",", lineterminator="\n"
                )
                writer.writeheader()
                for row in rows:
                    row["message_sent"] = "False"
                    writer.writerow(row)

                # Обрезаем файл на случай уменьшения размера
                f.truncate()

        except portalocker.exceptions.LockException as e:
            print(f"[!] Ошибка блокировки файла {csv_file_path}: {str(e)}")
        except Exception as e:
            print(f"[!] Ошибка при сбросе флагов: {str(e)}")

    @staticmethod
    async def mark_as_sent(csv_path: str, chat_url: str):
        """
        Обновляет флаг message_sent для указанного chat_url в CSV файле
        с блокировкой файла для безопасного доступа
        """
        try:
            with open(csv_path, "r+", encoding="utf-8") as f:
                portalocker.Lock(
                    f,
                    flags=portalocker.LOCK_EX | portalocker.LOCK_NB,
                    timeout=2.5,
                    check_interval=0.05,
                )

                reader = csv.reader(f)
                rows = list(reader)

                updated = False
                for row in rows:
                    if row[0] == chat_url:
                        row[1] = "True"
                        updated = True
                        break

                if updated:
                    f.seek(0)
                    writer = csv.writer(f, delimiter=",", lineterminator="\n")
                    writer.writerows(rows)
                    f.truncate()

        except portalocker.LockException:
            print(f"[~] Файл {csv_path} временно заблокирован, пробую снова...")
            await asyncio.sleep(0.1)
            return await CSVRepository.mark_as_sent(csv_path, chat_url)
        except Exception as e:
            print(f"[!] Ошибка блокировки: {str(e)}")

    @staticmethod
    def save_groups_to_csv(groups_data: List[Dict], filename: str) -> None:
        """
        Сохраняет данные о группах в CSV файл с указанными полями

        :param groups_data: Список словарей с данными о группах
        :param filename: Имя файла для сохранения результатов
        """
        if not groups_data:
            print("[!] Нет данных для сохранения")
            return

        os.makedirs("csv_databases", exist_ok=True)
        csv_path = os.path.join("csv_databases", f"{filename}.csv")

        fieldnames = ["link", "message_sent"]

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=fieldnames, delimiter=",", lineterminator="\n"
                )

                # Записываем заголовок
                writer.writeheader()

                # Записываем данные
                for group in groups_data:
                    writer.writerow(
                        {"link": group.get("link", ""), "message_sent": False}
                    )
            return csv_path
        except Exception as e:
            print(f"[!] Ошибка при сохранении файла: {str(e)}")
            return None
