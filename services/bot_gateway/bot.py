from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from .api.categories_service import CategoriesServiceClient
from .api.files_service import FilesServiceClient
from .api.requests_service import RequestsServiceClient
from .api.reporting_service import ReportingServiceClient
from .api.approvals_service import ApprovalsServiceClient
from .fsm.handlers import (
    BotDependencies,
    router as request_form_router,
    setup_request_form_handlers,
)


async def main() -> None:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    categories_url = os.getenv("CATEGORIES_SERVICE_URL", "http://categories_service:8001/api")
    requests_url = os.getenv("REQUESTS_SERVICE_URL", "http://requests_service:8000/api")
    files_url = os.getenv("FILES_SERVICE_URL", "http://files_service:8100")
    reporting_url = os.getenv("REPORTING_SERVICE_URL", "http://reporting_service:8200")
    approvals_url = os.getenv("APPROVALS_SERVICE_URL", "http://approvals_service:8002/api")

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    deps = BotDependencies(
        categories_client=CategoriesServiceClient(categories_url),
        requests_client=RequestsServiceClient(requests_url),
        files_client=FilesServiceClient(files_url),
        reporting_client=ReportingServiceClient(reporting_url),
        approvals_client=ApprovalsServiceClient(approvals_url),
    )
    setup_request_form_handlers(request_form_router, deps)
    dp.include_router(request_form_router)

    logging.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
