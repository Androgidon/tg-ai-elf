# Промпт для AI-агента: Telegram-бот с OpenRouter

## Задача
Создай минимальный Telegram-бот на Python, который получает сообщение от пользователя, отправляет его в OpenRouter API с системным промптом и возвращает ответ.

---

## Актуальные версии библиотек (декабрь 2025)

```
aiogram==3.23.0          # Релиз 7 декабря 2025
openrouter>=0.1.0        # Официальный Python SDK (бета)
python-dotenv>=1.0.0
```

**Python:** 3.10+

---

## Референсный код из официальной документации

### aiogram 3.23.0 — Базовый бот (из docs.aiogram.dev)

```python
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender
    """
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")

async def main() -> None:
    # Initialize Bot instance with default bot properties
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # And the run events dispatching
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
```

### OpenRouter Python SDK — Асинхронный вызов (из openrouter.ai/docs)

```python
from openrouter import OpenRouter
import asyncio
import os

async def main():
    async with OpenRouter(
        api_key=os.getenv("OPENROUTER_API_KEY")
    ) as client:
        response = await client.chat.send_async(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

### OpenRouter — Альтернатива через requests (если SDK не работает)

```python
import requests
import json

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer <OPENROUTER_API_KEY>",
        "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional
        "X-Title": "<YOUR_SITE_NAME>",      # Optional
    },
    data=json.dumps({
        "model": "anthropic/claude-sonnet-4-20250514",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the meaning of life?"}
        ]
    })
)
```

### OpenRouter — Асинхронная версия через aiohttp

```python
import aiohttp
import json

async def call_openrouter(messages: list, model: str, api_key: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages
            }
        ) as response:
            data = await response.json()
            return data["choices"][0]["message"]["content"]
```

---

## Требования к боту

### Структура
Один файл `main.py` — максимально простой MVP.

### Функциональность
1. Бот получает текстовое сообщение от пользователя
2. Отправляет его в OpenRouter API с заданным системным промптом
3. Показывает typing indicator пока ждёт ответ
4. Возвращает ответ пользователю

### Конфигурация через .env
```env
TELEGRAM_BOT_TOKEN=123456:ABC-xxx
OPENROUTER_API_KEY=sk-or-v1-xxx
MODEL=anthropic/claude-sonnet-4-20250514
SYSTEM_PROMPT=Ты советник по туризму b2b компании Centrum Holidays. Твоя задача отвечть по существу тур-агентам по запросам на туры. Опирайся на официальную информацию компаниии Centrum Air и Centrum Holidays в официальных источниках. Так же можешь направлять на систему бронирования туров Centrum Holidays. Задавай вопросы≤ на примере : пробовали ли вы бронировать тур через систему бронирований Centrum Holidays? Если у агента проблемы с системой то направляй на ответственного менеджера Centrum Holidays. Если ты не владеешь информацией, говоришь что перенаправишь вопрос b2b менеджеру",

```

### Обработка ошибок
- Если OpenRouter API недоступен → вернуть "⚠️ Ошибка AI, попробуй позже"
- Если сообщение пустое или не текст → игнорировать

---

## Критические моменты aiogram 3.x (НЕ ИСПОЛЬЗОВАТЬ устаревший синтаксис!)

### ❌ НЕПРАВИЛЬНО (aiogram 2.x — устарело):
```python
from aiogram import executor
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

dp = Dispatcher(bot, storage=MemoryStorage())
executor.start_polling(dp, skip_updates=True)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    ...
```

### ✅ ПРАВИЛЬНО (aiogram 3.23.0):
```python
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message) -> None:
    ...

@dp.message(Command("help"))
async def help_cmd(message: Message) -> None:
    ...

@dp.message()
async def handle_message(message: Message) -> None:
    ...

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Ключевые отличия aiogram 3.x:
- `@dp.message()` вместо `@dp.message_handler()`
- `CommandStart()` и `Command("name")` — фильтры из `aiogram.filters`
- `DefaultBotProperties` вместо передачи parse_mode напрямую
- `dp.start_polling(bot)` вместо `executor.start_polling(dp)`
- Нет `executor` модуля
- Нет `aiogram.contrib` — удалён

---

## Typing indicator (chat action)

```python
from aiogram.enums import ChatAction

@dp.message()
async def handle_message(message: Message) -> None:
    # Показать "печатает..." пока обрабатываем
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )
    
    # ... вызов AI API ...
    
    await message.answer(response_text)
```

---

## Ожидаемый результат

### main.py
Один файл с:
- Импортами aiogram 3.23.0
- Загрузкой .env через python-dotenv
- Обработчиком /start
- Обработчиком всех текстовых сообщений → отправка в OpenRouter → ответ
- Typing indicator
- Обработкой ошибок
- Запуском через asyncio.run(main())

### .env.example
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
MODEL=anthropic/claude-sonnet-4-20250514
SYSTEM_PROMPT=Ты дружелюбный помощник. Отвечай кратко и по делу.
```

---

## НЕ добавлять
- Базу данных
- Историю сообщений / память
- FSM (конечные автоматы)
- Middleware
- Логирование в файл
- Inline-кнопки
- Webhook режим
- Docker
- Любые усложнения

---

## Полезные модели OpenRouter для тестирования

| Модель | Описание |
|--------|----------|
| `anthropic/claude-sonnet-4-20250514` | Рекомендуемая, баланс цена/качество |
| `anthropic/claude-haiku-3.5` | Быстрая и дешёвая |
| `openai/gpt-4o-mini` | Дешёвая альтернатива |
| `google/gemini-2.0-flash-001` | Быстрая от Google |
| `meta-llama/llama-3.3-70b-instruct` | Open-source |

---

## Команда для запуска

```bash
# Установка зависимостей
pip install aiogram==3.23.0 openrouter python-dotenv

# Или если openrouter SDK не работает, использовать aiohttp:
pip install aiogram==3.23.0 aiohttp python-dotenv

# Запуск
python main.py
```
