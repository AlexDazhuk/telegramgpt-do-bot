# ---------------------------------
# Імпорти стандартних бібліотек
# ---------------------------------
import logging

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
    send_text_mix,
    send_text_buttons_raw
)

logger = logging.getLogger(__name__)


# ------------------------------------------------
# 💼 ДОПОМОГА З РЕЗЮМЕ — команда /resume_help
# ------------------------------------------------
async def resume_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартує режим збору інформації для резюме."""
    context.user_data.clear()

    await send_image(update, context, "7_resume_neon")

    context.user_data["conversation_state"] = "resume_get_name"

    await send_text_mix(
        update,
        context,
        "💼 Давайте створимо Ваше резюме!\n\n"
        "✍️ Почнемо. Напишіть будь-ласка, *Ваше імʼя та прізвище*."
    )


async def resume_collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Послідовно збирає дані для резюме: імʼя → освіта → досвід → навички."""
    text = update.message.text
    state = context.user_data["conversation_state"]

    # 1. Імʼя
    if state == "resume_get_name":
        context.user_data["resume_name"] = text
        context.user_data["conversation_state"] = "resume_get_education"

        return await send_text_mix(
            update,
            context,
            "🎓 Добре! Тепер напишіть інформацію про *Вашу освіту*.\n"
            "(ВНЗ, спеціальність, роки)"
        )

    # 2. Освіта
    if state == "resume_get_education":
        context.user_data["resume_education"] = text
        context.user_data["conversation_state"] = "resume_get_experience"

        return await send_text_mix(
            update,
            context,
            "💼 Чудово! Тепер опишіть *Досвід роботи*.\n"
            "(Компанія, посада, обовʼязки, роки)"
        )

    # 3. Досвід роботи
    if state == "resume_get_experience":
        context.user_data["resume_experience"] = text
        context.user_data["conversation_state"] = "resume_get_skills"

        return await send_text_mix(
            update,
            context,
            "🛠️ Супер! А тепер напишіть *Ваші ключові навички*."
        )

    # 4. Навички → Генерація резюме
    if state == "resume_get_skills":
        context.user_data["resume_skills"] = text
        context.user_data["conversation_state"] = "resume_done"

        return await generate_resume(update, context)


async def generate_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерує резюме через ChatGPT на основі зібраних даних."""
    prompt = load_prompt("resume_help")
    chat_gpt.set_prompt(prompt)

    name = context.user_data.get("resume_name", "")
    education = context.user_data.get("resume_education", "")
    experience = context.user_data.get("resume_experience", "")
    skills = context.user_data.get("resume_skills", "")

    msg = (
        f"Імʼя: {name}\n"
        f"Освіта: {education}\n"
        f"Досвід роботи: {experience}\n"
        f"Навички: {skills}\n"
        "Склади резюме у заданому форматі."
    )

    waiting = await send_text(update, context, "🔍 Формую ваше резюме...")

    try:
        resume_text = await chat_gpt.send_question(prompt, msg)
        await context.bot.delete_message(update.effective_chat.id, waiting.message_id)

        buttons = {
            "start": "🏁 Завершити",
            "resume_restart": "🔄 Почати заново"
        }

        await send_text_buttons_raw(
            update,
            context,
            f"📄 *Ваше резюме готове:*\n\n{resume_text}",
            buttons
        )

        context.user_data["conversation_state"] = "resume_result"

    except Exception as e:
        logger.error(f"Resume error: {e}")
        await send_text(update, context, "⚠️ Не вдалося сформувати резюме.")


async def resume_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        context.user_data.clear()
        return await start_screen(update, context)

    if data == "resume_restart":
        context.user_data.clear()
        return await resume_help_handler(update, context)
