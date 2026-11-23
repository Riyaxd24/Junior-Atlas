from __future__ import annotations

import asyncio
import logging

from pydantic import ValidationError

from bot.core.bot import Bot
from bot.core.config import ConfigurationError, Settings, validate_startup
from bot.core.logging import configure_logging


async def main() -> None:
    try:
        settings = Settings()
    except ValidationError as error:
        configure_logging('INFO')
        logging.getLogger('bot').error(
            'Invalid environment configuration. Check .env.example for the supported keys:\n%s',
            error,
        )
        raise SystemExit(2) from None
    configure_logging(settings.log_level)
    try:
        validate_startup(settings)
    except ConfigurationError as error:
        logging.getLogger('bot').error('Startup configuration error: %s', error)
        raise SystemExit(2) from None
    async with Bot(settings) as bot:
        await bot.start(settings.token)


if __name__ == '__main__':
    asyncio.run(main())
