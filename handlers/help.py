# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram import Update
from telegram.ext import ContextTypes

# ---------------------------------
# Імпорти локальних модулів
# ---------------------------------
# ✅ утиліти
from util import (
    load_message,
    send_text_mix,
    send_image
)


# ----------------------------------------------------
# 📘 Команда /help — показує довідку та список команд
# ----------------------------------------------------
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Надсилає користувачу файл довідки (help.txt)
    та зображення у стилі стартового екрана.
    """
    text = load_message("help")

    await send_image(update, context, "1_start_screen_neon")
    await send_text_mix(update, context, text)
