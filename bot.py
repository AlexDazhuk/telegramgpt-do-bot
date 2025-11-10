# ---------------------------------
# Імпорти стандартних бібліотек
# ---------------------------------
import logging

# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from colorama import Fore, Style, init as colorama_init
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters
)

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
# ✅ функції з інших хендлерів
from handlers.start import start_screen
from handlers.random import random_fact, random_fact_button_handler
from handlers.gpt import gpt_handler
from handlers.talk import talk_handler, talk_button_handler
from handlers.quiz import quiz_handler, quiz_button_handler
from handlers.translate import translate_handler, translate_button_handler
from handlers.resume import resume_help_handler, resume_button_handler
from handlers.message import message_handler

# ✅ конфігурація та логування
from credentials import BOT_TOKEN
from logging_config import setup_logging
from error_handler import handle_common_error

# ✅ утиліти
from util import default_callback_handler


# ------------------------------------------------------
# ✅ ОФІЦІЙНЕ МЕНЮ КОМАНД TELEGRAM
#     Цей блок встановлює список команд, які Telegram
#     показує у кнопці «Меню» для користувача.
# ------------------------------------------------------

async def setup_bot_commands(app):
    commands = [
        BotCommand("start", "Головне меню · 🌟"),
        BotCommand("random", "Випадковий факт · 🎲"),
        BotCommand("gpt", "Поставити запитання ChatGPT · 🤖"),
        BotCommand("talk", "Розмова з відомою особистістю · 👤"),
        BotCommand("quiz", "Пройти квіз · 🧠"),
        BotCommand("translate", "Перекладач · 🌐"),
        BotCommand("resume_help", "Допомога з резюме · 💼"),
    ]

    await app.bot.set_my_commands(commands)
    print("✅ MENU UPDATED — sent to Telegram")


# ---------------------------------
# ✅ Консольні кольори та логування
# ---------------------------------

# Ініціалізуємо кольори для консолі (Windows-friendly)
colorama_init(autoreset=True)

# Базове логування через стандартний логгер
setup_logging()
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Формат логування для різних рівнів
console_format = logging.Formatter(
    f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} "
    f"{Fore.YELLOW}%(levelname)s{Style.RESET_ALL} — %(message)s",
    datefmt="%H:%M:%S"
)


# ---------------------------------
# ✅ Ініціалізація Telegram-бота
# ---------------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

# ✅ автоматичне встановлення меню команд
app.post_init = setup_bot_commands


# -------------------------------------------
# ✅ Реєстрація всіх команд
# -------------------------------------------
app.add_handler(CommandHandler('start', start_screen))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_handler))
app.add_handler(CommandHandler('talk', talk_handler))
app.add_handler(CommandHandler('quiz', quiz_handler))
app.add_handler(CommandHandler('translate', translate_handler))
app.add_handler(CommandHandler('resume_help', resume_help_handler))


# -------------------------------------------
# ✅ Callback для кнопок Випадкових Фактів
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    random_fact_button_handler,
    pattern='^(random|start)$'
))

# -------------------------------------------
# ✅ Callback для TALK
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    talk_button_handler,
    pattern=r'^(talk_|start$)'
))

# -------------------------------------------
# ✅ Callback для QUIZ
#    тут обробляються:
#    - вибір теми (quiz_science…)
#    - наступне питання (quiz_next)
#    - змінити тему (quiz_change_topic)
#    - завершити (start)
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    quiz_button_handler,
    pattern=r'^(quiz_|quiz_next|quiz_change_topic|start$)'
))

# -------------------------------------------
# ✅ Callback для кнопок Перекладача
#    Обробляє:
#    - вибір мови (translate_*)
#    - зміну мови (translate_change)
#    - завершення (start)
# -------------------------------------------
app.add_handler(
    CallbackQueryHandler(
        translate_button_handler,
        pattern=r'^(translate_|translate_change|start$)'
    )
)

# ------------------------------------------------
# ✅ CALLBACK для РЕЗЮМЕ
# ------------------------------------------------
app.add_handler(CallbackQueryHandler(
    resume_button_handler,
    pattern=r'^(resume_restart|start$)'
))


# ✅ Загальний обробник текстових повідомлень
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# ✅ Fallback для кнопок без логіки
app.add_handler(CallbackQueryHandler(default_callback_handler))

# ✅ Обробник помилок
app.add_error_handler(handle_common_error)

# ✅ Запуск бота
app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
