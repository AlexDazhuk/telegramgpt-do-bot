# -----------------------------------------------
# util.py — допоміжні функції для TelegramGPT_DO
# -----------------------------------------------

from telegram import (
    Update, Message, InlineKeyboardButton,
    InlineKeyboardMarkup, BotCommand,
    MenuButtonCommands, MenuButtonDefault
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from pathlib import Path
import re


# ---------------------------
# ЕКРАНУВАННЯ MARKDOWN
# ---------------------------

def escape_markdown(text: str) -> str:
    """Екранує небезпечні символи для MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


# ---------------------------
# НАДСИЛАННЯ ТЕКСТУ
# ---------------------------

async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> Message:
    """Надсилає безпечне MarkdownV2 повідомлення."""
    safe = escape_markdown(text)
    return await context.bot.send_message(
        chat_id=update.effective_chat.id, text=safe, parse_mode=ParseMode.MARKDOWN_V2
    )


async def send_html(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> Message:
    """Надсилає HTML повідомлення."""
    return await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML
    )


async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict) -> Message:
    """Текст + inline кнопки"""
    safe = escape_markdown(text)
    keyboard = [[InlineKeyboardButton(v, callback_data=k)] for k, v in buttons.items()]
    markup = InlineKeyboardMarkup(keyboard)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=safe,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )


# ------------------------------------
# НАДСИЛАННЯ ЗОБРАЖЕНЬ (авто png/jpg)
# ------------------------------------

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> Message:
    """Автоматично відправляє .png або .jpg"""
    base = Path("resources/images")

    for ext in ("png", "jpg", "jpeg"):
        file = base / f"{name}.{ext}"
        if file.exists():
            with open(file, "rb") as img:
                return await context.bot.send_photo(update.effective_chat.id, img)

    return await send_text(update, context, f"⚠️ Зображення '{name}' не знайдено")


# ---------------------------
# МЕНЮ КОМАНД TELEGRAM
# ---------------------------

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, commands: dict):
    """Показати меню команд бота в чаті"""
    cmd = [BotCommand(k, v) for k, v in commands.items()]

    await context.bot.set_my_commands(cmd)
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonCommands()
    )


async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приховати кастомне меню в чаті"""
    await context.bot.delete_my_commands()
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id, menu_button=MenuButtonDefault()
    )


# -------------------------------------
# ЗАВАНТАЖЕННЯ ФАЙЛІВ (PROMPTS & TEXT)
# -------------------------------------

def load_message(name: str) -> str:
    with open(f"resources/messages/{name}.txt", encoding="utf8") as f:
        return f.read()


def load_prompt(name: str) -> str:
    with open(f"resources/prompts/{name}.txt", encoding="utf8") as f:
        return f.read()


# -----------------------------------
# ОБРОБНИК ЗАМОВЧУВАННЯ ДЛЯ CALLBACK
# -----------------------------------

async def default_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback для кнопок без обробника"""
    query = update.callback_query
    await query.answer()

    await send_text(
        update, context,
        f"Натиснута кнопка: {query.data}\n(але для неї ще нема логіки 😅)"
    )


# ---------------------------
# ІНДИКАТОР "БОТ ДРУКУЄ..."
# ---------------------------

async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показує 'бот друкує...' на 2 секунди"""
    await context.bot.send_chat_action(update.effective_chat.id, "typing")


# ---------------------------
# НАДСИЛАННЯ ДОКУМЕНТІВ
# ---------------------------

async def send_document(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str):
    """Надсилає файл"""
    with open(filepath, "rb") as f:
        return await context.bot.send_document(update.effective_chat.id, f)


# -----------------------------
# ПОВІДОМЛЕННЯ З ПРОГРЕС-БАРОМ
# -----------------------------

async def send_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, current: int, total: int, text="⏳ Обробка..."):
    """Надсилає прогрес бар у стилі Telegram"""
    bar_length = 20
    filled = int(current / total * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)

    msg = f"{text}\n\n{bar} {current}/{total}"

    return await send_text(update, context, msg)


# ---------------------------
# ПРОСТИЙ АНТИСПАМ
# ---------------------------

from time import time
user_last_action = {}

def anti_spam(limit_seconds=2):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        now = time()

        if uid in user_last_action and now - user_last_action[uid] < limit_seconds:
            await send_text(update, context, "⚠️ Повільніше, будь ласка ⏳")
            return False

        user_last_action[uid] = now
        return True

    return wrapper


# ---------------------------
# СТАРТОВИЙ ЕКРАН
# ---------------------------

async def start_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає неоновий старт-екран з кнопкою"""
    await send_image(update, context, "1.0_start_screen_neon")

    text = (
        "🌌 *Вітаю у світі TelegramGPT_DO* ⚡\n\n"
        "🤖 Я твій AI-помічник\n"
        "Можеш:\n"
        "• Дізнаватися факти 🎲\n"
        "• Чатитись як з ChatGPT 💬\n"
        "• Говорити з легендами 🧠\n"
        "• Грати в квізи 🏆\n"
        "• Перекладати текст 🌐\n\n"
        "_Натисни кнопку нижче, щоб почати_ ✨"
    )

    buttons = {"start": "🚀 Почати"}
    await send_text_buttons(update, context, text, buttons)