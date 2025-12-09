import asyncio
import logging
import sys
from sqlalchemy.future import select

# Adjust path to find modules if run directly
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soccer_platform.database import engine, Base, get_db
from soccer_platform.models import User
from soccer_platform.auth import get_password_hash

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CreateAdmin")

async def create_admin(username, password):
    logger.info(f"Creating admin user: {username}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # We need a session, using the engine directly for simplicity in a script
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check existing
        result = await session.execute(select(User).where(User.username == username))
        existing = result.scalars().first()
        
        if existing:
            logger.warning(f"User {username} already exists. Updating role to admin.")
            existing.role = "admin"
            existing.hashed_password = get_password_hash(password)
            await session.commit()
            logger.info("Updated successfully.")
            return

        # Create new
        new_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            role="admin"
        )
        session.add(new_user)
        await session.commit()
        logger.info(f"Admin {username} created successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create a Superuser/Admin")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default="admin123", help="Admin password")
    
    args = parser.parse_args()
    
    asyncio.run(create_admin(args.username, args.password))
