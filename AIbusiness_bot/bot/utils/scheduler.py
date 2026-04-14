from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.database import clear_old_orders
from bot.config import ORDER_RETENTION_DAYS
import logging

logger = logging.getLogger(__name__)


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    return scheduler


async def cleanup_old_orders_task():
    try:
        deleted_count = await clear_old_orders(ORDER_RETENTION_DAYS)
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old orders (older than {ORDER_RETENTION_DAYS} days)")
    except Exception as e:
        logger.error(f"Error during orders cleanup: {e}")


def schedule_cleanup_jobs(scheduler: AsyncIOScheduler):
    scheduler.add_job(
        cleanup_old_orders_task,
        trigger=CronTrigger(hour=3, minute=0),
        id='cleanup_old_orders',
        name='Cleanup old completed orders',
        replace_existing=True
    )
