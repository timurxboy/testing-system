from aiogram import Router

from apps.bot.handlers.menu import router as menu_router
from apps.bot.handlers.start import router as start_router
from apps.bot.handlers.stats import router as stats_router
from apps.bot.handlers.testing import router as testing_router


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(start_router)
    root.include_router(menu_router)
    root.include_router(testing_router)
    root.include_router(stats_router)
    return root
