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
from handlers.resume import resume_collect_data
from handlers.quiz import quiz_check_answer

# ✅ ChatGPT сервіс
from gpt_instance import chat_gpt

# ✅ утиліти
from util import (
    load_prompt,
    send_text,
    send_text_buttons
)

logger = logging.getLogger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Головний обробник текстових повідомлень користувача.
    Обробляє режими: QUIZ → GPT → TALK → або без режиму.
    """
    message_text = update.message.text
    state = context.user_data.get("conversation_state")

    # ✅ 1) Режим створення резюме
    if state and state.startswith("resume_"):
        return await resume_collect_data(update, context)

    # ✅ 2) КВІЗ — якщо чекаємо відповідь, обробляємо її ПЕРШИМИ
    if state == "quiz_waiting_answer":
        return await quiz_check_answer(update, context, message_text)

    # ✅ 3) Якщо режим ще не визначено — пробуємо здогадатися
    if not state:
        recognized = await interpret_random_input(update, context, message_text)
        if not recognized:
            await show_funny_response(update, context)
        return

    # ✅ 4) Режим GPT
    if state == "gpt":
        waiting = await send_text(update, context, "🔍 Обробляю ваше питання…")
        try:
            response = await chat_gpt.add_message(message_text)
            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)
            await send_text(update, context, f"🤖 *Відповідь ChatGPT:*\n\n{response}")
        except Exception as e:
            logger.error(f"GPT error: {e}")
            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)
            await send_text(update, context, "😔 Сталася помилка. Спробуйте пізніше.")
        return

    # ✅ 5) Режим TALK (діалог з відомою особистістю)
    if state == "talk":
        personality = context.user_data.get("selected_personality")

        if not personality:
            return await send_text(update, context, "😕 Спочатку виберіть особистість командою /talk")

        waiting = await send_text(update, context, "🔍 Обробляю…")

        try:
            response = await chat_gpt.add_message(message_text)
            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)

            await send_text_buttons(
                update,
                context,
                f"👤 *{personality.replace('talk_', '').capitalize()}:*\n\n{response}",
                {"start": "🏁 Закінчити"}
            )
        except Exception as e:
            logger.error(f"TALK error: {e}")
            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)
            await send_text(update, context, "😔 Сталася помилка. Спробуйте пізніше.")
        return

    # ✅ 6) Режим Перекладача
    if state == "translate":
        lang = context.user_data.get("translate_lang")

        if not lang:
            return await send_text(update, context, "🌐 Спочатку оберіть мову: /translate")

        prompt = load_prompt(lang)
        chat_gpt.set_prompt(prompt)

        waiting = await send_text(update, context, "🔍 Перекладаю...")

        try:
            translation = await chat_gpt.send_question(prompt, message_text)

            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)

            # Кнопки дій
            buttons = {
                "translate_change": "🌐 Змінити мову",
                "start": "🏁 Завершити"
            }

            await send_text_buttons(
                update,
                context,
                f"📘 *Переклад:*\n\n{translation}",
                buttons
            )

        except Exception as e:
            logger.error(f"Translate error: {e}")
            await context.bot.delete_message(update.effective_chat.id, waiting.message_id)
            await send_text(update, context, "⚠️ Помилка перекладу. Спробуйте пізніше.")
        return


async def interpret_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> bool:
    """
    Аналізує текст повідомлення та визначає намір користувача.
    Повертає True, якщо намір розпізнано і оброблено.
    """
    text = message_text.lower()

    # ✅ /random — Випадковий факт
    if any(w in text for w in ('факт', 'facts', 'random', 'випадков')):
        await send_text(update, context, "🧠 Бачу, вас цікавлять факти!")
        from handlers.random import random_fact
        await random_fact(update, context)
        return True

    # ✅ /gpt — ChatGPT
    if any(w in text for w in ('gpt', 'чат', 'питання', 'запита', 'дізнатися')):
        await send_text(update, context, "🤖 Перемикаю в режим ChatGPT…")
        from handlers.gpt import gpt_handler
        await gpt_handler(update, context)
        return True

    # ✅ /talk — Розмова з легендою
    if any(w in text for w in ('розмов', 'говори', 'особист', 'легенд', 'talk')):
        await send_text(update, context, "👤 Хочете поговорити з легендою? Вмикаю режим…")
        from handlers.talk import talk_handler
        await talk_handler(update, context)
        return True

    # ✅ /quiz — Квіз
    if any(w in text for w in ('квіз', 'вікторин', 'quiz', 'питання тест')):
        await send_text(update, context, "🧠 Починаємо квіз! Готую теми…")
        from handlers.quiz import quiz_handler
        await quiz_handler(update, context)
        return True

    # ✅ /translate — Перекладач
    if any(w in text for w in ('переклад', 'translate', 'перекладач', 'перекласти')):
        await send_text(update, context, "🌐 Перемикаю в режим перекладу…")
        from handlers.translate import translate_handler
        await translate_handler(update, context)
        return True

    # ✅ /resume_help — допомога з резюме
    if any(w in text for w in ('резюме', 'resume', 'cv', 'робота', 'help resume')):
        await send_text(update, context, "💼 Розпочинаємо створення резюме!")
        from handlers.resume import resume_help_handler
        await resume_help_handler(update, context)
        return True

    # ❌ Нічого не розпізнано
    return False


async def show_funny_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показує випадкову кумедну відповідь, якщо намір не визначено.
    """
    import random

    funny = [
        "🤔 Хмм… Я трохи заплутався.",
        "🧐 Дуже цікаво! Але не дуже схоже на команду.",
        "😅 Ого! Оце повідомлення!",
        "🤖 *Перезавантаження нейромереж…*",
        "🦄 Це виглядає магічно, але незрозуміло.",
        "🕵️ Аналізую ваше повідомлення…",
        "🎲 Випадкове повідомлення? Випадковий бот!",
        "📱 *тисне кнопки* Так… ні… все ще не те…",
        "🌈 Незвично, але мені подобається 😄",
        "🤓 Алгоритми розгубилися, але я тримаюсь!",
    ]

    hints = [
        "🤖 Хочете поставити питання? Використайте /gpt",
        "🎲 Спробуйте /random — цікавий факт вас чекає",
        "👤 Хочете поговорити з легендою? Команда /talk",
        "🧠 Перевірте знання — введіть /quiz",
        "🌐 Потрібен переклад? Використайте /translate",
        "💼 Створити резюме? Спробуйте /resume_help",
        "🏠 Повернутися в меню — /start",
    ]

    response = f"{random.choice(funny)}\n\n💡 Підказка: {random.choice(hints)}"

    await send_text(update, context, response)

    # Після жарту — повернення на головний екран
    await start_screen(update, context)

