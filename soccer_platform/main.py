from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import aiofiles
import os

from .database import engine, Base, get_db
from .models import Game, Event
from . import models # Access to Team, User, etc explicitly
from . import schemas # For Pydantic models used in body
from .schemas import GameCreate, GameUpdate, EventCreate, GameSchema, GameSummary
from .config import settings

# Email
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Soccer Platform API")



# Mail Configuration
mail_conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_FROM_NAME = settings.MAIL_FROM_NAME,
    MAIL_STARTTLS = settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = settings.USE_CREDENTIALS,
    VALIDATE_CERTS = settings.VALIDATE_CERTS
)

# Serve Frontend Static Assets
# Should point to soccer_platform/frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Serve Videos (MVP Storage)
video_dir = os.path.join(os.path.dirname(__file__), "../videos") # Mapped in Docker
if not os.path.exists(video_dir):
    os.makedirs(video_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=video_dir), name="videos")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/game.html")
async def read_game_page():
    return FileResponse(os.path.join(frontend_dir, "game.html"))

@app.get("/login")
async def read_login_page():
    return FileResponse(os.path.join(frontend_dir, "login.html"))

from .scheduler import scheduler_service
from .database import engine, Base, get_db, AsyncSessionLocal

async def nightly_sync_job():
    """Wrapper to run sync with its own DB session"""
    print("⏰ Nightly Sync Started")
    async with AsyncSessionLocal() as db:
        try:
            from .services.teamsnap import teamsnap_service
            # We need to act as admin? sync_roster doesn't check role, only endpoints do.
            result = await teamsnap_service.sync_full(db)
            print(f"✅ Nightly Sync Finished: {result}")
        except Exception as e:
            print(f"❌ Nightly Sync Failed: {e}")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # WARNING: DESTRUCTIVE
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
            # Note: If this was a raw table and is now a class, ensure columns exist
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

# --- AUTHENTICATION ---
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import auth
from .models import User
from .schemas import Token, UserCreate, UserResponse
from fastapi import status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Check existing
    res = await db.execute(select(User).where(User.username == user.username))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Username taken")
        
    hashed = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        hashed_password=hashed,
        role=user.role,
        full_name=user.full_name,
        jersey_number=user.jersey_number
    )
    
    # Handle M2M Teams
    if user.team_ids:
        # Fetch teams to ensure they exist/valid
        teams_res = await db.execute(select(models.Team).where(models.Team.id.in_(user.team_ids)))
        teams = teams_res.scalars().all()
        
        # db.add(new_user) must happen before we get ID usually, but we can add new_user to session
        # However, to create associations we need new_user to be in session or attached.
        
        for t in teams:
            assoc = models.UserTeam(user=new_user, team=t, jersey_number=user.jersey_number)
            db.add(assoc)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Eager load teams for response
    # Re-fetch with teams loaded
    from sqlalchemy.orm import selectinload
    stmt = select(models.User).options(selectinload(models.User.teams)).where(models.User.id == new_user.id)
    result = await db.execute(stmt)
    return result.scalars().first()

@app.get("/api/users", response_model=List[schemas.UserResponse])
async def list_users(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin" and 'coach' not in current_user.role: # Allow coaches? Or just admin?
        # User requested per-user creds, so let's lock this down to admin for now.
        raise HTTPException(status_code=403, detail="Not authorized")
    from sqlalchemy.orm import selectinload
    # Load associations then the team details
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.team_associations).selectinload(models.UserTeam.team))
    )
    users = result.scalars().all()
    # Pydantic via from_attributes alias check:
    # User model has 'team_associations'. Schema has 'teams'.
    # We can create a lightweight wrapper or rely on schema handling if we name schema field 'team_associations'.
    # But for API cleanliness 'teams' is better.
    # Quick fix: Rename property in User model OR map it manually here.
    # Manual map is safest.
    
    resp = []
    for u in users:
        # Construct teams list from associations
        teams_data = []
        for assoc in u.team_associations:
            teams_data.append({
                "team": assoc.team,
                "jersey_number": assoc.jersey_number
            })
        
        # We need to build the UserResponse dict
        resp.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "full_name": u.full_name,
            "nickname": u.nickname,
            "teams": teams_data
        })
    return resp

@app.post("/api/teams/sync")
async def sync_teamsnap(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from .services.teamsnap import teamsnap_service
    result = await teamsnap_service.sync_full(db)
    return result

@app.put("/api/me/teamsnap_creds")
async def update_my_teamsnap_creds(creds: schemas.UserTeamsnapCredsUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user:
         raise HTTPException(status_code=401)
    
    current_user.teamsnap_client_id = creds.client_id
    current_user.teamsnap_client_secret = creds.client_secret
    db.add(current_user)
    await db.commit()
    return {"status": "ok", "message": "Credentials updated"}

@app.get("/settings.html")
async def read_settings_page():
    return FileResponse(os.path.join(frontend_dir, "settings.html"))

@app.post("/api/teams", response_model=schemas.TeamResponse)
async def create_team(team: schemas.TeamCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import uuid
    new_team = models.Team(
        id=str(uuid.uuid4()),
        name=team.name,
        season=team.season,
        league=team.league,
        birth_year=team.birth_year
    )
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team

@app.get("/api/teams", response_model=List[schemas.TeamResponse])
async def list_teams(db: AsyncSession = Depends(get_db)):
    # Allow read by authenticated users (verified by Depends(get_db) implicitly if used correctly, 
    # but here we might want to check current_user if strictly private)
    result = await db.execute(select(models.Team))
    return result.scalars().all()

@app.post("/api/settings/teamsnap_exchange")
async def exchange_teamsnap(req: schemas.TeamSnapExchangeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from .services.teamsnap import teamsnap_service
    try:
        print(f"DEBUG: Exchange Request Received. ClientID: {req.client_id[:5]}..., RedirectURI: {req.redirect_uri}")
        res = await teamsnap_service.exchange_token(db, req.client_id, req.client_secret, req.code, req.redirect_uri, user=current_user)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/admin.html")
async def read_admin_page():
    return FileResponse(os.path.join(frontend_dir, "admin.html"))

@app.get("/roster_matrix.html")
async def read_roster_matrix_page():
    return FileResponse(os.path.join(frontend_dir, "roster_matrix.html"))

# --- SETTINGS CRUD ---
# SettingItem is in schemas.py

@app.get("/api/settings", response_model=List[schemas.SettingItem])
async def get_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
        
    result = await db.execute(select(models.SystemSetting))
    
    sensitive_keys = ["TEAMSNAP_TOKEN", "MAIL_PASSWORD"]
    out = []
    for s in result.scalars().all():
        if s.key in sensitive_keys:
            continue
        out.append({"key": s.key, "value": s.value})
    return out

@app.post("/api/settings")
async def update_settings(settings: List[schemas.SettingItem], current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    
    from .database import set_sql_debug

    for s in settings:
        if s.value == "********":
            continue
            
        if s.key == "sql_debug":
             is_debug = s.value.lower() == "true"
             set_sql_debug(is_debug)
             
        # Upsert
        existing = await db.get(models.SystemSetting, s.key)
        if existing:
            existing.value = s.value
        else:
            new_s = models.SystemSetting(key=s.key, value=s.value)
            db.add(new_s)
    
    await db.commit()
    return {"status": "updated"}

# --- GAMES MANAGEMENT ---

@app.get("/api/games", response_model=List[schemas.GameSummary])
async def list_games(
    team_id: Optional[str] = None, 
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(models.Game).order_by(models.Game.date.desc())
    
    # Filter by user teams if not admin
    if current_user.role != "admin":
        # Get user team IDs
        # We need to eager load or query associations? 
        # Actually User model has team_associations (UserTeam).
        # We can do a join or filter by team_id in subquery.
        
        # Simpler: Get list of team IDs from user object (needs eager load in get_current_user or separate query)
        # Let's do a subquery join for efficiency
        
        # stmt = stmt.join(models.UserTeam, models.Game.team_id == models.UserTeam.team_id)\
        #            .where(models.UserTeam.user_id == current_user.id)
        
        # Or just use the association properly
        subq = select(models.UserTeam.team_id).where(models.UserTeam.user_id == current_user.id)
        stmt = stmt.where(models.Game.team_id.in_(subq))

    if team_id:
        stmt = stmt.where(models.Game.team_id == team_id)
    if status:
        stmt = stmt.where(models.Game.status == status)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@app.post("/api/games/{game_id}/match")
async def match_game_video(
    game_id: str, 
    body: schemas.GameUpdate, # reusing update schema which has optional video_path
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["admin", "coach"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    game = await db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if body.video_path is not None:
        game.video_path = body.video_path
        
    await db.commit()
    return {"status": "updated", "video_path": game.video_path}

@app.get("/games.html")
async def read_games_page():
    return FileResponse(os.path.join(frontend_dir, "games.html"))



@app.patch("/api/games/{game_id}", response_model=schemas.GameSchema)
async def update_game(
    game_id: str, 
    game_update: schemas.GameUpdate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin" and current_user.role != "coach":
        raise HTTPException(status_code=403)
        
    game = await db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game_update.video_path is not None:
        game.video_path = game_update.video_path
        # Use full path? Or relative? 
        # Typically frontend sends full path or filename. 
        # We can validate existence here if we want.
        
    if game_update.status is not None:
        game.status = game_update.status
        
    await db.commit()
    await db.refresh(game)
    return game


@app.post("/api/games", response_model=GameSchema)
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    db_game = await db.get(Game, game.id)
    if db_game:
        # Already exists, return it
        return db_game
    
    new_game = Game(id=game.id, status=game.status, date=game.date)
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    return new_game



@app.get("/api/games/{game_id}/social")
async def get_social_clip(game_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Triggers generation of a 9:16 vertical clip.
    Returns status: 'processing' or 'ready'.
    """
    db_game = await db.get(Game, game_id)
    if not db_game or not db_game.video_path:
        raise HTTPException(status_code=404, detail="Game or video not found")

    # Resolve paths
    # URL: /videos/xyz.mp4 -> File: ../videos/xyz.mp4
    filename = os.path.basename(db_game.video_path)
    base_dir = os.path.join(os.path.dirname(__file__), "../videos")
    abs_video_path = os.path.join(base_dir, filename)
    abs_output_path = abs_video_path.replace(".mp4", "_vertical.mp4")
    
    # Check cache
    if os.path.exists(abs_output_path):
        return {"status": "ready", "url": db_game.video_path.replace(".mp4", "_vertical.mp4")}

    # Get events for tracking
    result = await db.execute(select(Event).where(Event.game_id == game_id))
    events = result.scalars().all()
    
    # Trigger background task
    from .services.social import generate_vertical_clip
    background_tasks.add_task(generate_vertical_clip, game_id, abs_video_path, events)
    
    return {"status": "processing", "message": "Vertical clip generation started. Check back in 1 minute."}

@app.patch("/api/games/{game_id}", response_model=GameSchema)
async def update_game(game_id: str, update: GameUpdate, db: AsyncSession = Depends(get_db)):
    db_game = await db.get(Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if update.video_path:
        db_game.video_path = update.video_path
    if update.status:
        db_game.status = update.status
        
    await db.commit()
    await db.refresh(db_game)
    return db_game

@app.post("/api/games/{game_id}/events")
async def add_events(game_id: str, events: List[EventCreate], db: AsyncSession = Depends(get_db)):
    db_game = await db.get(Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    for e in events:
        new_event = Event(
            game_id=game_id,
            timestamp=e.timestamp,
            frame=e.frame,
            type=e.type,
            event_metadata=e.event_metadata
        )
        db.add(new_event)
    
    await db.commit()
    return {"status": "added", "count": len(events)}

@app.post("/api/games/{game_id}/video")
async def upload_game_video(game_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Save file to /videos directory
    # Ensure directory exists (mapped volume)
    videos_path = os.path.join(os.path.dirname(__file__), "../videos")
    os.makedirs(videos_path, exist_ok=True)
    
    file_path = os.path.join(videos_path, f"{game_id}.mp4")
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            # Read in chunks
            while content := await file.read(1024 * 1024): # 1MB chunks
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # Update DB
    db_game = await db.get(Game, game_id)
    if db_game:
        db_game.video_path = f"/videos/{game_id}.mp4"
        db_game.status = "processed"
        await db.commit()
        await db.refresh(db_game)

        # TRIGGER EMAIL NOTIFICATION
        try:
            # 1. Fetch System Settings for Mail
            from .models import SystemSetting
            settings_res = await db.execute(select(SystemSetting).where(SystemSetting.key.in_([
                "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_PORT", "MAIL_SERVER"
            ])))
            db_settings = {s.key: s.value for s in settings_res.scalars().all()}
            
            # Use DB settings or Fallback to Env
            username = db_settings.get("MAIL_USERNAME", settings.MAIL_USERNAME)
            password = db_settings.get("MAIL_PASSWORD", settings.MAIL_PASSWORD)
            mail_from = db_settings.get("MAIL_FROM", settings.MAIL_FROM)
            port = int(db_settings.get("MAIL_PORT", settings.MAIL_PORT))
            server = db_settings.get("MAIL_SERVER", settings.MAIL_SERVER)
            
            if not server or not username:
                print("Mail not configured via DB or Env. Skipping.")
            else:
                conf = ConnectionConfig(
                    MAIL_USERNAME = username,
                    MAIL_PASSWORD = password,
                    MAIL_FROM = mail_from,
                    MAIL_PORT = port,
                    MAIL_SERVER = server,
                    MAIL_FROM_NAME = settings.MAIL_FROM_NAME, # Keep static or add DB
                    MAIL_STARTTLS = True, # Assume true for most modern
                    MAIL_SSL_TLS = False,
                    USE_CREDENTIALS = True,
                    VALIDATE_CERTS = False 
                )
                
                # 2. Get recipients (Admins & Coaches)
                query = select(User).where(User.role.in_(["admin", "coach"]))
                result = await db.execute(query)
                users = result.scalars().all()
                
                # Filter valid emails
                recipients = [u.username for u in users if "@" in u.username]
                
                if recipients:
                    message = MessageSchema(
                        subject=f"Game Processed: {game_id}",
                        recipients=recipients,
                        body=f"The game {game_id} has been processed and is ready for viewing.",
                        subtype=MessageType.html
                    )
                    
                    fm = FastMail(conf)
                    await fm.send_message(message)
                    print(f"Sent notifications to {recipients}")
                    
        except Exception as e:
            print(f"Failed to send email: {e}")

    return {"status": "uploaded", "url": f"/videos/{game_id}.mp4"}

@app.get("/api/games", response_model=List[GameSummary])
async def list_games(db: AsyncSession = Depends(get_db)):
    # Using GameSchema (with events) caused LazyLoad errors and perf issues.
    # Switching to GameSchema (but without events loaded) - wait, if schema requires events, it will fail.
    # I need to change response_model to GameSummary (defined in schemas.py)
    # But I can't import it inside function. 
    # Let's rely on correct import in main.py updates.
    result = await db.execute(select(Game).order_by(Game.date.desc()))
    return result.scalars().all()

@app.get("/api/search")
async def search_events(q: str, db: AsyncSession = Depends(get_db)):
    """
    Semantic-ish search. 
    In V1: ILIKE on event types.
    Future: Embedding vector search.
    """
    if not q: return []
    
    # Simple keyword match
    # "Show me goals" -> type='goal'
    query = select(Event).join(Game).where(Event.type.ilike(f"%{q}%")).order_by(Event.timestamp)
    # Also search metadata? (e.g. "player_count": 5)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Format for UI
    return [{
        "game_id": e.game_id,
        "time": e.timestamp,
        "type": e.type,
        "desc": f"{e.type} at {int(e.timestamp)}s"
    } for e in events]

@app.get("/api/games/{game_id}", response_model=GameSchema)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Game).options(selectinload(Game.events)).where(Game.id == game_id)
    )
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
