"""
logging_config.py — модуль для налаштування логування в TelegramGPT_DO.

Створює файл логів (logs/bot.log) і виводить повідомлення в консоль.
Логи використовуються для відстеження роботи бота, помилок та статистики.
"""


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from colorama import Fore, Style, init as colorama_init


def setup_logging(log_dir: str = "logs", log_file: str = "bot.log"):
    """
    Налаштовує логування:
    - створює директорію для логів, якщо її немає
    - веде логування в консоль (з кольорами) і у файл із ротацією
    - рівень: INFO
    """
    colorama_init(autoreset=True)

    log_dir_path = Path(__file__).resolve().parent / log_dir
    log_dir_path.mkdir(exist_ok=True)
    log_path = log_dir_path / log_file

    # Формат без кольорів (для файлу)
    file_format = "[%(asctime)s] [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    file_formatter = logging.Formatter(file_format, "%Y-%m-%d %H:%M:%S")

    # Формат із кольорами (для консолі)
    console_formatter = logging.Formatter(
        f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} "
        f"{Fore.YELLOW}[%(levelname)s]{Style.RESET_ALL} "
        f"{Fore.GREEN}%(name)s{Style.RESET_ALL}:%(funcName)s:%(lineno)d — %(message)s",
        "%H:%M:%S"
    )

    # --- Хендлер для файлу ---
    file_handler = RotatingFileHandler(
        log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    # --- Хендлер для консолі ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # --- Основна конфігурація ---
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )

    logging.getLogger(__name__).info(f"✅ Логування ініціалізовано. Файл: {log_path}")


def get_logger(name: str) -> logging.Logger:
    """Повертає логер з вказаним ім’ям."""
    return logging.getLogger(name)
