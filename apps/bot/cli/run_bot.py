import asyncio

from apps.bot.runner import run_polling
from core.logging import setup_logger


def main() -> None:
    setup_logger(name="bot")
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
