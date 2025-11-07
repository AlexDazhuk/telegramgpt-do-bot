# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram import Update
from telegram.ext import ContextTypes

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
# ✅ утиліти
from util import (
    load_message,
    send_image,
    send_text,
    show_main_menu
)


# ---------------------------------
# 🏁 Команда /start — головне меню
# ---------------------------------
async def start_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # видалення попередніх станів розмови

    text = load_message('main')
    await send_image(update, context, '1_start_screen_neon')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Випадковий факт',
        'gpt': 'Поставити запитання ChatGPT',
        'talk': 'Розмова з відомою особистістю',
        'quiz': 'Пройти квіз та перевірити знання',
        'translate': 'Перекладач',
        'resume_help': 'Допомога з резюме'
    })
