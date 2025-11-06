"""
error_handler.py — глобальна обробка помилок для TelegramGPT_DO.
"""

from telegram.ext import CallbackContext
from telegram.error import Conflict, NetworkError, BadRequest
from loguru import logger


async def handle_common_error(update: object, context: CallbackContext):
    error = context.error

    # Спеціальна обробка окремих типів
    if isinstance(error, Conflict):
        logger.error("⚠️ Інший екземпляр бота вже запущено.")
        return

    if isinstance(error, NetworkError):
        logger.error(f"⚠️ Помилка мережі: {error}")
        return

    if isinstance(error, BadRequest):
        logger.warning(f"⚠️ Помилка Telegram API: {error}")
        return

    # Загальний лог для всіх інших помилок
    logger.error(f"🚨 Виникла помилка: {error}")

    # Повідомлення користувачу, якщо можливо
    try:
        if update and hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Вибач, сталася неочікувана помилка."
            )
    except Exception as e:
        logger.error(f"⚡ Не вдалося надіслати повідомлення про помилку: {e}")
