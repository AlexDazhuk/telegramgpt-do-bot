# -----------------------------------------------
# util.py — допоміжні функції для TelegramGPT_DO
# -----------------------------------------------

from telegram import (
    Update, Message, InlineKeyboardButton,
    InlineKeyboardMarkup, BotCommand,
    MenuButtonCommands
)

from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from pathlib import Path
import re


# ---------------------------
# ЕКРАНУВАННЯ MARKDOWN
# ---------------------------

def escape_markdown_partial(text: str) -> str:
    """
    Екранує небезпечні символи MarkdownV2, але НЕ чіпає *жирний*.
    """
    # символи MarkdownV2 (крім *)
    to_escape = r'([_~`>#+\-=|{}.!()])'
    return re.sub(to_escape, r'\\\1', text)


def protect_markdown_blocks(text: str):
    """
    Витягує markdown-блоки типу *жирний*, _курсив_, `код`
    і захищає їх від екранування.
    """
    pattern = r'(\*.*?\*|_.*?_|\~.*?\~|`.*?`)'
    parts = re.split(pattern, text)

    result = []
    for part in parts:
        if re.match(pattern, part):
            # Не чіпаємо markdown-блок
            result.append(part)
        else:
            # Екрануємо всю іншу частину
            result.append(escape_markdown_partial(part))
    return "".join(result)


# ---------------------------
# НАДСИЛАННЯ ТЕКСТУ
# ---------------------------

async def send_text(update, context, text: str):
    """Надсилає безпечний MarkdownV2 текст."""
    safe = escape_markdown(text, version=2)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=safe,
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def send_text_mix(update, context, text: str):
    """
    Розумне надсилання тексту у MarkdownV2.
    Зберігає markdown, але екранує всі інші небезпечні символи.
    """
    safe_text = protect_markdown_blocks(text)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=safe_text,
        parse_mode="MarkdownV2"
    )


async def send_text_raw(update, context, text: str):
    """
    Надсилає сирий текст із MarkdownV2 без будь-якої обробки.
    Використовується для випадків, де форматування задається вручну.
    """
    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def send_text_buttons(update, context, text: str, buttons: dict):
    """Відправка тексту з MarkdownV2 з екрануванням + кнопки."""
    safe = escape_markdown(text, version=2)

    keyboard = [[InlineKeyboardButton(v, callback_data=k)] for k, v in buttons.items()]
    markup = InlineKeyboardMarkup(keyboard)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=safe,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def send_text_buttons_mix(update, context, raw_text: str, buttons: dict):
    """
    raw_text — текст, який може містити *жирні* елементи, його НЕ екрануємо.
    Але ВСЕ, що після заголовка, потрібно екранувати вручну (safe_fact).
    """

    keyboard = [[InlineKeyboardButton(v, callback_data=k)] for k, v in buttons.items()]
    markup = InlineKeyboardMarkup(keyboard)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=raw_text,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def send_text_buttons_raw(update, context, text: str, buttons: dict):
    """
    Надсилає текст із кнопками. Використовує MarkdownV2,
    тому застосовується часткове екранування.
    """
    safe_text = escape_markdown_partial(text)

    keyboard = [[InlineKeyboardButton(v, callback_data=k)] for k, v in buttons.items()]
    markup = InlineKeyboardMarkup(keyboard)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=safe_text,
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


# -------------------------------------
# ЗАВАНТАЖЕННЯ ФАЙЛІВ (PROMPTS & TEXT)
# -------------------------------------

def load_message(name: str) -> str:
    """
    Завантажує текстове повідомлення з каталогу resources/messages.
    """
    with open(f"resources/messages/{name}.txt", encoding="utf8") as f:
        return f.read()


def load_prompt(name: str) -> str:
    """
    Завантажує промпт із каталогу resources/prompts.
    """
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
# НАДСИЛАННЯ ДОКУМЕНТІВ
# ---------------------------

async def send_document(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str):
    """Надсилає файл"""
    with open(filepath, "rb") as f:
        return await context.bot.send_document(update.effective_chat.id, f)


async def send_wait(update, context, text="🔍 Обробляю…"):
    """
    Надсилає службове повідомлення "завантаження" без Markdown,
    щоб уникнути помилок парсингу.
    """
    chat_id = update.effective_chat.id

    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=None  # ❗ без розмітки, щоб не впасти
        )
        return msg
    except Exception as e:
        print("WAIT ERROR:", e)
        return None


async def safe_delete(bot, chat_id, message_id):
    """
    Безпечно видаляє повідомлення. Ігнорує помилки, якщо його не існує.
    """
    if not message_id:
        return

    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass
