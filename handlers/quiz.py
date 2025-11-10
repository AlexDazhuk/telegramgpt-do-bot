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
    send_text_raw,
    send_text_buttons,
    send_text_buttons_raw
)

logger = logging.getLogger(__name__)


# ------------------------------------------------
# 🧠 КВІЗ — команда /quiz
# ------------------------------------------------
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартує режим квізу: показує список тем.
    """
    context.user_data.clear()

    # Стартове фото
    await send_image(update, context, "5_quiz_neon")

    # Теми квізу
    topics = {
        "quiz_science": "🔬 Наука",
        "quiz_history": "📜 Історія",
        "quiz_tech": "💻 Технології",
        "quiz_space": "🛰️ Космос",
        "quiz_random": "🎲 Мікс",
        "start": "🏁 Завершити"
    }

    context.user_data["conversation_state"] = "quiz_select_topic"

    await send_text_buttons(
        update,
        context,
        "❓ Оберіть тему квізу:",
        topics
    )


async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє кнопки у квізі: вибір теми, нове питання, зміна теми, завершення.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    # Завершення квізу
    if data == "start":
        context.user_data.clear()
        return await start_screen(update, context)

    # Якщо користувач хоче інше питання тієї ж теми
    if data == "quiz_next":
        return await quiz_generate_question(update, context)

    # Якщо користувач хоче змінити тему
    if data == "quiz_change_topic":
        return await quiz_handler(update, context)

    # Якщо вибрано тему
    if data.startswith("quiz_"):
        context.user_data.clear()
        context.user_data["conversation_state"] = "quiz_question"
        context.user_data["quiz_topic"] = data
        context.user_data["correct"] = 0
        context.user_data["total"] = 0
        return await quiz_generate_question(update, context)


async def quiz_generate_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерує нове питання квізу через ChatGPT.
    """
    topic = context.user_data["quiz_topic"]

    # Прив'язуємо промпт (наприклад: prompts/quiz_science.txt)
    prompt = load_prompt(topic)
    chat_gpt.set_prompt(prompt)

    waiting = await send_text(update, context, "🔍 Генерую питання...")

    try:
        question = await chat_gpt.send_question(
            prompt,
            "Згенеруй одне чітке питання квізу без відповіді."
        )

        await context.bot.delete_message(update.effective_chat.id, waiting.message_id)

        context.user_data["conversation_state"] = "quiz_waiting_answer"
        context.user_data["current_question"] = question

        await send_text_raw(update, context, f"❓ *Питання:*\n\n{question}\n\n✍️ Напишіть вашу відповідь:")

    except Exception as e:
        logger.error(f"Quiz error: {e}")
        await send_text(update, context, "⚠️ Не вдалось згенерувати питання.")


async def quiz_check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_answer: str):
    """
    Відправляє відповідь користувача ChatGPT та отримує оцінку.
    """
    question = context.user_data["current_question"]
    prompt = load_prompt(context.user_data["quiz_topic"])
    chat_gpt.set_prompt(prompt)

    waiting = await send_text(update, context, "🔍 Перевіряю відповідь...")

    try:
        # Отримуємо оцінку від ChatGPT
        result = await chat_gpt.send_question(
            prompt,
            f"Ось питання: {question}\nОсь відповідь користувача: {user_answer}\n"
            "Оціни відповідь. Напиши коротко: правильно чи ні, дай коротке пояснення."
        )

        await context.bot.delete_message(update.effective_chat.id, waiting.message_id)

        # ✅ Обробка статистики
        context.user_data["total"] += 1

        result_clean = result.strip().lower()

        # Ключові слова для визначення правильності
        negative = ("неправ", "невір", "wrong", "incorrect")
        positive = ("правильно", "вірно", "correct")

        # ✅ Перевірка на “неправильно” (пріоритет)
        if result_clean.startswith(negative):
            is_correct = False
        elif result_clean.startswith(positive):
            is_correct = True
        else:
            # резерв–евристика (якщо раптом промпт дав щось інше)
            is_correct = (
                any(p in result_clean for p in positive) and
                not any(n in result_clean for n in negative)
            )

        # ✅ Оновлюємо рахунок
        if is_correct:
            context.user_data["correct"] += 1

        score = (
            f"✅ Правильних: {context.user_data['correct']}\n"
            f"❔ Всього: {context.user_data['total']}"
        )


        # Кнопки дій
        buttons = {
            "quiz_next": "🔄 Наступне питання",
            "quiz_change_topic": "🗂 Змінити тему",
            "start": "🏁 Завершити"
        }

        # Відправляємо результат
        await send_text_buttons_raw(
            update,
            context,
            f"📘 *Результат:*\n\n{result}\n\n📊 *Ваш рахунок:*\n{score}",
            buttons
        )

        context.user_data["conversation_state"] = "quiz_question"

    except Exception as e:
        logger.error(f"Quiz check error: {e}")
        await send_text(update, context, "⚠️ Помилка перевірки відповіді.")
