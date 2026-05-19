import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from apps.bot.handlers import build_root_router
from apps.bot.middlewares.db import DbSessionMiddleware
from core.db.session import SessionLocal
from core.settings import core_settings

logger = logging.getLogger("bot")


def build_bot() -> Bot:
    if not core_settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    return Bot(
        token=core_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=core_settings.BOT_PARSE_MODE),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    db_middleware = DbSessionMiddleware(session_factory=SessionLocal)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)

    dp.include_router(build_root_router())
    return dp


async def run_polling() -> None:
    bot = build_bot()
    dispatcher = build_dispatcher()

    logger.info("Starting bot polling")
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot polling stopped")
