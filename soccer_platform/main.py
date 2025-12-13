from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import engine, Base, AsyncSessionLocal
from .config import settings
from .scheduler import scheduler_service
from .routers import auth, users, teams, games, settings as settings_router, frontend

app = FastAPI(title="Soccer Platform API")

# --- Static Files ---
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
video_dir = os.path.join(os.path.dirname(__file__), "../videos") 

if not os.path.exists(video_dir):
    os.makedirs(video_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
app.mount("/videos", StaticFiles(directory=video_dir), name="videos")

# --- Include Routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(games.router)
app.include_router(settings_router.router)
app.include_router(frontend.router)


# --- Startup & Shutdown ---

async def nightly_sync_job():
    """Wrapper to run sync with its own DB session"""
    logger.info("⏰ Nightly Sync Started")
    async with AsyncSessionLocal() as db:
        try:
            from .services.teamsnap import teamsnap_service
            # We need to act as admin? sync_roster doesn't check role, only endpoints do.
            result = await teamsnap_service.sync_full(db)
            logger.info(f"✅ Nightly Sync Finished: {result}")
        except Exception:
            logger.error("❌ Nightly Sync Failed", exc_info=True)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Manual Migration for new columns (Safe if exists)
        from sqlalchemy import text
        try:
            # Users
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_data JSONB"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_token VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_client_id VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_client_secret VARCHAR"))
            
            # Teams
            await conn.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS teamsnap_data JSONB"))
            
            # Games
            await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS teamsnap_data JSONB"))
            await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS teamsnap_id VARCHAR"))
            await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS location VARCHAR"))
            await conn.execute(text("ALTER TABLE games ADD COLUMN IF NOT EXISTS is_home BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_games_teamsnap_id ON games (teamsnap_id)"))

            # UserTeams (Association)
            await conn.execute(text("ALTER TABLE user_teams ADD COLUMN IF NOT EXISTS jersey_number INTEGER"))
            
            print("✅ Schema migration checks complete.")
        except Exception as e:
            print(f"⚠️ Schema migration warning: {e}")

    
    # Start Scheduler
    scheduler_service.start()
    # Add Nightly Job (e.g. 3 AM)
    scheduler_service.add_job(nightly_sync_job, trigger_type='cron', hour=3, minute=0)

    # Run Seeder
    from .services.seeder import seed_demo_data
    try:
        await seed_demo_data()
    except Exception as e:
        print(f"Seeder failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    scheduler_service.stop()
