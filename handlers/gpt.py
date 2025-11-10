# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram.constants import ParseMode
from telegram import Update
from telegram.ext import ContextTypes

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
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

    # 1. Зображення
    await send_image(update, context, '3_gpt_neon')

    # 2. Промпт
    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)

    # 3. Текст у MarkdownV2
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🤖 *ChatGPT активовано\\.*\n"
            "Надішліть своє запитання — і я одразу відповім\\."
        ),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    # 4. Стан
    context.user_data['conversation_state'] = 'gpt'