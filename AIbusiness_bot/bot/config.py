import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "business_bot.db")
ORDER_RETENTION_DAYS = int(os.getenv("ORDER_RETENTION_DAYS", "30"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID must be set in .env file")
