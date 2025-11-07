# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram import Update
from telegram.ext import ContextTypes

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
# ✅ функції з інших хендлерів
# from handlers.start import start_screen

# ✅ ChatGPT сервіс
from gpt_instance import chat_gpt

# ✅ утиліти
from util import (
    load_prompt,
    send_image
)


# ---------------------------------
# 🤖 ChatGPT режим — команда /gpt
# ---------------------------------
async def gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    # 1. Надсилаємо зображення (через оновлену send_image)
    await send_image(update, context, '3_gpt_neon')

    # 2. Завантажуємо промпт
    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)

    # 3. Текст у HTML
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🤖 <b>ChatGPT активовано.</b>\n"
            "Надішліть своє запитання — і я одразу відповім."
        ),
        parse_mode="HTML"
    )

    # 4. Установлюємо стан
    context.user_data['conversation_state'] = 'gpt'
