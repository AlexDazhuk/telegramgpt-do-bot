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
    send_text_buttons
)

logger = logging.getLogger(__name__)


# -------------------------------------
# 🎲 Випадковий факт — команда /random
# -------------------------------------
# Максимальна кількість збережених фактів в історії
MAX_FACT_HISTORY = 25


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає випадковий факт з урахуванням кешу."""

    # 1. Показуємо картинку
    await send_image(update, context, '2_random_fact_neon')

    # 2. Повідомлення про пошук
    loading_msg = await send_text(update, context, "🔍 Шукаю щось цікаве...")

    try:
        # Інціалізуємо кеш фактів
        used_facts = context.user_data.get("used_facts", [])

        prompt = load_prompt('random')

        # 3. Отримуємо новий факт, який не повторюється
        fact = None
        attempts = 0
        new_fact = None

        while attempts < 5:      # 5 спроб знайти унікальний факт
            new_fact = await chat_gpt.send_question(
                prompt,
                "Дай мені один цікавий факт, коротко."
            )

            if new_fact not in used_facts:
                fact = new_fact
                break

            attempts += 1

        # Якщо всі 5 спроб були невдалими — просто приймаємо останній
        if fact is None:
            fact = new_fact

        # Додаємо факт у кеш
        used_facts.append(fact)

        # Обрізаємо кеш, якщо він надто великий
        if len(used_facts) > MAX_FACT_HISTORY:
            used_facts = used_facts[-MAX_FACT_HISTORY:]

        context.user_data["used_facts"] = used_facts

        # 4. Видаляємо "Шукаю..."
        await context.bot.delete_message(update.effective_chat.id, loading_msg.message_id)

        # 5. Кнопки
        buttons = {
            'random': 'Хочу ще факт 🔄',
            'start': 'Закінчити 🏁'
        }

        await send_text_buttons(
            update,
            context,
            f"🚀 <b>Випадковий факт від AI:<b>\n\n{fact}",
            buttons
        )

    except Exception as e:
        logger.error(f"Помилка при отриманні випадкового факту: {e}")

        await context.bot.delete_message(update.effective_chat.id, loading_msg.message_id)

        await send_text(
            update, context,
            "😔 На жаль, виникла помилка при отриманні факту. Спробуйте пізніше."
        )


# ✅ Користувацький обробник кнопок випадкових фактів
async def random_fact_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # обов'язково відповідаємо Telegram

    data = query.data

    if data == 'random':
        # користувач натиснув "Хочу ще факт"
        return await random_fact(update, context)

    elif data == 'start':
        # користувач натиснув "Закінчити"
        return await start_screen(update, context)
