# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram import Update
from telegram.ext import ContextTypes

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
# ✅ функції з інших хендлерів
from handlers.start import start_screen

# ✅ ChatGPT сервіс
from gpt_instance import chat_gpt

# ✅ утиліти
from util import (
    load_prompt,
    send_image,
    send_text,
    send_text_buttons
)


# ------------------------------------------------
# 🌐 ПЕРЕКЛАДАЧ — команда /translate
# ------------------------------------------------
async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартує режим перекладача:
        - показує список доступних мов.
    """
    context.user_data.clear()

    await send_image(update, context, "6_translate_neon")

    languages = {
        "translate_en": "🇬🇧 Англійська",
        "translate_ua": "🇺🇦 Українська",
        "translate_de": "🇩🇪 Німецька",
        "translate_pl": "🇵🇱 Польська",
        "translate_es": "🇪🇸 Іспанська",
        "start": "🏁 Завершити"
    }

    context.user_data["conversation_state"] = "translate_select_lang"

    await send_text_buttons(
        update,
        context,
        "🌐 Оберіть мову перекладу:",
        languages
    )


async def translate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє кнопки у режимі перекладача:
        - вибір мови
        - зміна мови
        - завершення
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ Завершити
    if data == "start":
        context.user_data.clear()
        return await start_screen(update, context)

    # ✅ Змінити мову
    if data == "translate_change":
        return await translate_handler(update, context)

    # ✅ Вибір мови
    if data.startswith("translate_"):
        lang = data.replace("translate_", "")
        context.user_data.clear()

        context.user_data["conversation_state"] = "translate"
        context.user_data["translate_lang"] = data

        prompt = load_prompt(data)
        chat_gpt.set_prompt(prompt)

        await send_text(
            update,
            context,
            f"✅ Мову обрано. Тепер надішліть текст, який потрібно перекласти."
        )
