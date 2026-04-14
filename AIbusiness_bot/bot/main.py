import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import user_handlers, admin_handlers
from bot.utils.scheduler import setup_scheduler, schedule_cleanup_jobs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting bot...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    
    # Setup scheduler for cleanup jobs
    scheduler = setup_scheduler()
    schedule_cleanup_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started")
    
    # Start polling
    try:
        logger.info("Bot is running!")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
