# apps/backend/app/database.py
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
# Ganti skema ke asyncpg supaya SQLAlchemy jalan secara async
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True)

# Dibuat sekali di level modul, dipakai ulang oleh FastAPI dan bot Telegram
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with SessionLocal() as session:
        yield session
