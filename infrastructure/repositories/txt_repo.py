import os
from typing import List


class TxtRepository:
    
    @staticmethod
    def save_channels_to_txt(urls: List[str], filename: str) -> str:
        """
        Сохраняет список каналов в текстовый файл, по одному URL на строку.

        :param urls: Список строк с URL каналов
        :param filename: База имени файла (без расширения)
        :return: Полный путь к сохранённому файлу
        """
        output_dir = "monitoring_channels"
        os.makedirs(output_dir, exist_ok=True)

        # Гарантируем, что имя файла заканчивается на .txt
        if not filename.lower().endswith(".txt"):
            filename = f"{filename}.txt"
        path = os.path.join(output_dir, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                for url in urls:
                    f.write(f"{url}\n")
            return path
        except Exception as e:
            print(f"[!] Ошибка при сохранении в {path}: {e}")
            return None