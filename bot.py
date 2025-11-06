# ---------------------------------
# Імпорти стандартних бібліотек
# ---------------------------------
import logging

# ---------------------------------
# Імпорти сторонніх бібліотек
# ---------------------------------
from colorama import Fore, Style, init as colorama_init
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ---------------------------------
# Імпорти локальних модулів застосунку
# ---------------------------------
from credentials import BOT_TOKEN, ChatGPT_TOKEN
from error_handler import handle_common_error
from gpt import ChatGptService
from logging_config import setup_logging
from util import (
    default_callback_handler,
    load_message,
    load_prompt,
    send_image,
    send_text,
    send_text_buttons,
    show_main_menu
)

# ---------------------------------
# Консольні кольори та логування
# ---------------------------------

# Ініціалізуємо кольори для консолі (Windows-friendly)
colorama_init(autoreset=True)

# Базове логування через стандартний логгер
setup_logging()
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Формат логування для різних рівнів
console_format = logging.Formatter(
    f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} "
    f"{Fore.YELLOW}%(levelname)s{Style.RESET_ALL} — %(message)s",
    datefmt="%H:%M:%S"
)


# ---------------------------------
# Ініціалізація сервісів
# ---------------------------------
# Сервіс ChatGPT
chat_gpt = ChatGptService(ChatGPT_TOKEN)

# Telegram-бот
app = ApplicationBuilder().token(BOT_TOKEN).build()


# ---------------------------------
# 🏁 Команда /start — головне меню
# ---------------------------------
async def start_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # видалення попередніх станів розмови

    text = load_message('main')
    await send_image(update, context, '1_start_screen_neon')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Випадковий факт',
        'gpt': 'Поставити запитання ChatGPT',
        'talk': 'Розмова з відомою особистістю',
        'quiz': 'Пройти квіз та перевірити знання',
        'translate': 'Перекладач',
        'resume_help': 'Допомога з резюме'
    })


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


async def interpret_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> bool:
    """
    Аналізує текст повідомлення та визначає намір користувача.
    Повертає True, якщо намір розпізнано і оброблено.
    """
    text = message_text.lower()

    if any(w in text for w in ('факт', 'цікав', 'random', 'випадков')):
        await send_text(update, context, "🧠 Бачу, вас цікавлять факти!")
        await random_fact(update, context)
        return True

    if any(w in text for w in ('gpt', 'чат', 'питання', 'запита', 'дізнатися')):
        await send_text(update, context, "🤖 Перемикаю в режим ChatGPT…")
        await gpt_handler(update, context)
        return True

    if any(w in text for w in ('розмов', 'говори', 'спілкува', 'особист', 'talk')):
        await send_text(update, context, "👤 Хочете поговорити з легендою? Зараз…")
        await talk_handler(update, context)
        return True

    return False


async def show_funny_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показує випадкову кумедну відповідь, якщо намір не визначено.
    """
    import random

    funny = [
        "🤔 Хмм… Не зовсім зрозумів вас.",
        "🧐 Дуже цікаво! Але це не схоже на команду.",
        "😅 Ого! Ви мене заплутали.",
        "🤖 *Перезавантаження мозку…*",
        "🦄 Це виглядає магічно, але не як команда.",
        "🕵️ Досліджую ваше повідомлення…",
        "🎲 Випадкове повідомлення? Випадковий бот!",
        "📱 *тисне кнопки* Так… ні… не те…",
        "🌈 Красиво, але незрозуміло.",
        "🤓 Мої алгоритми розгубилися.",
    ]

    hints = [
        "Спробуйте /gpt, щоб поставити питання",
        "Введіть /random, щоб отримати цікавий факт",
        "Команда /talk — діалог з легендою",
        "Не знаєте, що обрати? Використайте /start",
    ]

    response = f"{random.choice(funny)}\n\n💡 Підказка: {random.choice(hints)}"
    await send_text(update, context, response)

    await start_screen(update, context)


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

        personality_name = data.replace('talk_', '').capitalize()

        await send_image(update, context, data)

        await send_text_buttons(
            update, context,
            f"👤 Ви обрали *{personality_name}*. Напишіть повідомлення, щоб почати діалог.",
            {'start': 'Закінчити 🏁'}
        )


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

        await send_text(update, context, f"❓ *Питання:*\n\n{question}\n\n✍️ Напишіть вашу відповідь:")

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
        await send_text_buttons(
            update,
            context,
            f"📘 *Результат:*\n\n{result}\n\n📊 *Ваш рахунок:*\n{score}",
            buttons
        )

        context.user_data["conversation_state"] = "quiz_question"

    except Exception as e:
        logger.error(f"Quiz check error: {e}")
        await send_text(update, context, "⚠️ Помилка перевірки відповіді.")


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


# ------------------------------------------------
# 💼 ДОПОМОГА З РЕЗЮМЕ — команда /resume_help
# ------------------------------------------------
async def resume_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартує режим збору інформації для резюме."""
    context.user_data.clear()

    await send_image(update, context, "7_resume_neon")

    context.user_data["conversation_state"] = "resume_get_name"

    await send_text(
        update,
        context,
        "💼 Давайте створимо ваше резюме!\n\n"
        "✍️ Почнімо. Напишіть, будь ласка, *ваше імʼя та прізвище*."
    )


async def resume_collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Послідовно збирає дані для резюме: імʼя → освіта → досвід → навички."""
    text = update.message.text
    state = context.user_data["conversation_state"]

    # 1. Імʼя
    if state == "resume_get_name":
        context.user_data["resume_name"] = text
        context.user_data["conversation_state"] = "resume_get_education"

        return await send_text(
            update,
            context,
            "🎓 Добре! Тепер напишіть інформацію про *вашу освіту*.\n"
            "(ВНЗ, спеціальність, роки)"
        )

    # 2. Освіта
    if state == "resume_get_education":
        context.user_data["resume_education"] = text
        context.user_data["conversation_state"] = "resume_get_experience"

        return await send_text(
            update,
            context,
            "💼 Чудово! Тепер опишіть *досвід роботи*.\n"
            "(Компанія, посада, обовʼязки, роки)"
        )

    # 3. Досвід роботи
    if state == "resume_get_experience":
        context.user_data["resume_experience"] = text
        context.user_data["conversation_state"] = "resume_get_skills"

        return await send_text(
            update,
            context,
            "🛠️ Супер! А тепер напишіть *ваші ключові навички*."
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

        await send_text_buttons(
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


# -------------------------------------------
# ✅ Реєстрація всіх команд
# -------------------------------------------
app.add_handler(CommandHandler('start', start_screen))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_handler))
app.add_handler(CommandHandler('talk', talk_handler))
app.add_handler(CommandHandler('quiz', quiz_handler))
app.add_handler(CommandHandler('translate', translate_handler))
app.add_handler(CommandHandler('resume_help', resume_help_handler)) # тимчасово

# -------------------------------------------
# ✅ Callback для кнопок Випадкових Фактів
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    random_fact_button_handler,
    pattern='^(random|start)$'
))

# -------------------------------------------
# ✅ Callback для TALK
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    talk_button_handler,
    pattern=r'^(talk_|start$)'
))

# -------------------------------------------
# ✅ Callback для QUIZ
#    тут обробляються:
#    - вибір теми (quiz_science…)
#    - наступне питання (quiz_next)
#    - змінити тему (quiz_change_topic)
#    - завершити (start)
# -------------------------------------------
app.add_handler(CallbackQueryHandler(
    quiz_button_handler,
    pattern=r'^(quiz_|quiz_next|quiz_change_topic|start$)'
))

# -------------------------------------------
# ✅ Callback для кнопок Перекладача
#    Обробляє:
#    - вибір мови (translate_*)
#    - зміну мови (translate_change)
#    - завершення (start)
# -------------------------------------------
app.add_handler(
    CallbackQueryHandler(
        translate_button_handler,
        pattern=r'^(translate_|translate_change|start$)'
    )
)

# ------------------------------------------------
# ✅ CALLBACK для РЕЗЮМЕ
# ------------------------------------------------
app.add_handler(CallbackQueryHandler(
    resume_button_handler,
    pattern=r'^(resume_restart|start$)'
))

# -------------------------------------------
# ✅ Загальний обробник текстових повідомлень
# -------------------------------------------
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# -------------------------------------------
# ✅ Fallback для кнопок без логіки
# -------------------------------------------
app.add_handler(CallbackQueryHandler(default_callback_handler))

# -------------------------------------------
# ✅ Обробник помилок
# -------------------------------------------
app.add_error_handler(handle_common_error)

# -------------------------------------------
# ✅ Запуск бота
# -------------------------------------------
app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
