import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.errors import BadRequestResponseError, PaymentRequiredResponseError

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY")
MODEL = getenv("MODEL", "anthropic/claude-sonnet-4")
SYSTEM_PROMPT = getenv(
    "SYSTEM_PROMPT",
    "Ты советник по туризму b2b компании Centrum Holidays. Твоя задача отвечть по существу тур-агентам по запросам на туры. Опирайся на официальную информацию компаниии Centrum Air и Centrum Holidays в официальных источниках. Так же можешь направлять на систему бронирования туров Centrum Holidays. Задавай вопросы≤ на примере : пробовали ли вы бронировать тур через систему бронирований Centrum Holidays? Если у агента проблемы с системой то направляй на ответственного менеджера Centrum Holidays. Если ты не владеешь информацией, говоришь что перенаправишь вопрос b2b менеджеру",
)

dp = Dispatcher()


def _assistant_content_to_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                t = item.get("text")
                if isinstance(t, str):
                    parts.append(t)
            elif hasattr(item, "text") and getattr(item, "text", None):
                parts.append(str(getattr(item, "text")))
        return "\n".join(parts) if parts else str(content)
    return str(content)


async def call_openrouter(user_text: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    async with OpenRouter(api_key=OPENROUTER_API_KEY) as client:
        result = await client.chat.send_async(model=MODEL, messages=messages)
    if not result.choices:
        return ""
    text = _assistant_content_to_text(result.choices[0].message.content)
    return text.strip()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name or 'друг')}! "
        "Подскажи чем могу помочь?"
    )


@dp.message(F.text)
async def text_message_handler(message: Message) -> None:
    raw = message.text or ""
    if not raw.strip():
        return

    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    try:
        reply = await call_openrouter(raw)
    except PaymentRequiredResponseError:
        await message.answer(
            "Пожалуйста обратитесь к менеджеру."
        )
        return
    except BadRequestResponseError as e:
        logging.warning("OpenRouter bad request: %s", e)
        await message.answer(
            "⚠️ Неверные настройки модели или запроса. "
            "Проверь MODEL в .env (актуальные ID: https://openrouter.ai/models ). "
            f"Детали: {e}"
        )
        return
    except Exception:
        logging.exception("OpenRouter request failed")
        reply = ""

    if not reply:
        await message.answer("⚠️ Ошибка AI, попробуй позже")
    else:
        await message.answer(reply)


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан в .env")
    if not OPENROUTER_API_KEY:
        raise SystemExit("OPENROUTER_API_KEY не задан в .env")

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
