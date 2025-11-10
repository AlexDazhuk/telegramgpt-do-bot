# ---------------------------------
# Імпорти стандартних бібліотек
# ---------------------------------
import logging

# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

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
    send_text_buttons,
    send_text_buttons_raw
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------
# 👤 Діалог з відомою особистістю — команда /talk
# -----------------------------------------------------------
async def talk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /talk.
    Показує список доступних відомих особистостей для діалогу.
    """
    context.user_data.clear()

    await send_image(update, context, '4_famous_people_neon')

    # Меню вибору особистостей
    personalities = {
        'talk_steve_jobs': 'Стів Джобс (Apple) 💡',
        'talk_elon_musk': 'Ілон Маск (SpaceX) 🚀',
        'talk_marie_curie': 'Марія Кюрі (Науковиця) ⚗️',
        'talk_leonardo_da_vinci': 'Леонардо да Вінчі (Митець) 🎨',
        'talk_nikola_tesla': 'Нікола Тесла (Винахідник) ⚡',
        'talk_albert_einstein': 'Альберт Ейнштейн (Фізик) 🧠',
        'start': 'Закінчити 🏁'
    }

    context.user_data['conversation_state'] = 'talk'

    await send_text_buttons(
        update, context,
        "👤 Оберіть легенду і почніть діалог 👇",
        personalities
    )


async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє натискання кнопок у режимі TALK.
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ Завершити діалог
    if data == 'start':
        context.user_data.clear()
        await start_screen(update, context)
        return

    # ✅ Вибір особистості
    if data.startswith('talk_'):
        context.user_data.clear()

        context.user_data['selected_personality'] = data
        context.user_data['conversation_state'] = 'talk'

        prompt = load_prompt(data)
        chat_gpt.set_prompt(prompt)

        personality_name = data.replace('talk_', '').replace('_', ' ').title()

        await send_image(update, context, data)

        safe_name = escape_markdown(personality_name, version=2)

        await send_text_buttons_raw(
            update,
            context,
            f"👤 Ви обрали *{safe_name}*.\nНапишіть повідомлення, щоб почати діалог.",
            {'start': 'Закінчити 🏁'}
        )
