"""
gpt_instance.py
----------------
Містить єдиний глобальний екземпляр ChatGPT-сервісу,
який використовується в усіх модулях проєкту.
"""

from credentials import ChatGPT_TOKEN
from gpt_service import ChatGptService

# Єдиний глобальний екземпляр сервісу ChatGPT
chat_gpt = ChatGptService(ChatGPT_TOKEN)
