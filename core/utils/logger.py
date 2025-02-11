import logging
import os


def setup_logger():
    """Настройка логирования"""
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    logging.basicConfig(
        filename=os.path.join(log_directory, "mybot.log"),  # Путь к лог-файлу
        filemode="a",  # Режим добавления (append) в файл
        format="%(asctime)s - %(levelname)s - %(message)s",  # Формат логов
        level=logging.INFO,  # Уровень логирования: INFO
        encoding="utf-8",  # Кодировка UTF-8
    )
    # Возвращаем настроенный логгер
    return logging.getLogger(__name__)


# Инициализация логгера
logger = setup_logger()
