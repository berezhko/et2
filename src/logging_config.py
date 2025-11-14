# logging_config.py
import logging
import os

from src.path_project import project_dir

class ConsoleFormatter(logging.Formatter):
    def __init__(self):
        # Создаём разные форматы
        self.notset_formatter = logging.Formatter(
            "◻️  %(levelname)s: %(message)s"
        )
        self.debug_formatter = logging.Formatter(
            "🔍  %(levelname)s: %(message)s"
        )
        self.info_formatter = logging.Formatter(
            "ℹ️  %(levelname)s: %(message)s"
        )
        self.warning_formatter = logging.Formatter(
            "⚠️  %(levelname)s: %(message)s"
        )
        self.error_formatter = logging.Formatter(
            "❗  %(levelname)s: %(message)s"
        )
        self.critical_formatter = logging.Formatter(
            "💥  %(levelname)s: %(message)s"
        )

    def format(self, record):
        if record.levelno > logging.ERROR:
            return self.critical_formatter.format(record)
        elif record.levelno == logging.ERROR:
            return self.error_formatter.format(record)
        elif record.levelno == logging.WARNING:
            return self.warning_formatter.format(record)
        elif record.levelno == logging.INFO:
            return self.info_formatter.format(record)
        elif record.levelno == logging.DEBUG:
            return self.debug_formatter.format(record)
        else:
            return self.notset_formatter.format(record)


def setup_logging(app):
    """
    Настраивает корневой логгер.
    Вызывать один раз в начале программы.
    """
    log_dir = project_dir() / "log/"
    os.makedirs(log_dir, exist_ok=True)
    # Уровень корневого логгера — самый низкий из нужных
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Очищаем существующие обработчики (на случай повторного вызова)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Обработчик для файла
    file_handler = logging.FileHandler(f"{log_dir}/{app}.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # ← только WARNING, ERROR и CRITICAL
    console_handler.setFormatter(ConsoleFormatter())

    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
