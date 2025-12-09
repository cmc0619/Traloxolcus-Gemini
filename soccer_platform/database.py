from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# usage of postgresql+asyncpg scheme is required for async engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://soccer:soccerpassword@db:5432/soccer_platform")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
