from openai import OpenAI
import httpx


class ChatGptService:
    """
    Сервіс роботи з ChatGPT API:
    - зберігає історію повідомлень
    - дозволяє працювати з промптом
    - підтримує одинарні запити (send_question)
    - підтримує діалог (add_message)
    """

    client: OpenAI = None
    message_list: list = None

    def __init__(self, token: str):
        """
        Ініціалізація клієнта OpenAI.
        Якщо токен починається з 'gpt:', він конвертується у справжній формат.
        """
        token = (
            "sk-proj-" + token[:3:-1]
            if token.startswith("gpt:")
            else token
        )

        self.client = OpenAI(
            http_client=httpx.Client(
                proxy="http://18.199.183.77:49232"
            ),
            api_key=token
        )

        self.message_list = []

    async def send_message_list(self) -> str:
        """
        Відправляє весь список повідомлень у ChatGPT
        та повертає текст відповіді.
        """
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",      # можна замінити на gpt-4o / mini
            messages=self.message_list,
            max_tokens=3000,
            temperature=0.9
        )

        message = completion.choices[0].message
        self.message_list.append(message)

        return message.content

    def set_prompt(self, prompt_text: str) -> None:
        """
        Встановлює системний промпт та очищає історію діалогу.
        """
        self.message_list.clear()
        self.message_list.append({
            "role": "system",
            "content": prompt_text
        })

    async def add_message(self, message_text: str) -> str:
        """
        Додає нове повідомлення від користувача
        та повертає відповідь ChatGPT (у діалоговому режимі).
        """
        self.message_list.append({
            "role": "user",
            "content": message_text
        })

        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        """
        Відправляє одноразове питання:
        - очищає історію
        - встановлює промпт
        - додає текст питання
        """
        self.message_list.clear()

        self.message_list.append({
            "role": "system",
            "content": prompt_text
        })

        self.message_list.append({
            "role": "user",
            "content": message_text
        })

        return await self.send_message_list()
