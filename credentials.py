"""
Модуль credentials.py
---------------------
Завантажує токени з файлу .env та надає їх іншим модулям.
"""

import os
from dotenv import load_dotenv

# Завантажує .env у змінні середовища
load_dotenv()

# Токени (залишаємо назви змінних такими, як у коді)
ChatGPT_TOKEN = os.getenv("OPENAI_API_KEY", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
