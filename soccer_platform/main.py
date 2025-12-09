from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import aiofiles
import os

from .database import engine, Base, get_db
from .models import Game, Event
from .schemas import GameCreate, GameUpdate, EventCreate, GameSchema

from .models import Game, Event
from .schemas import GameCreate, GameUpdate, EventCreate, GameSchema

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Soccer Platform API")

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

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
            metadata=e.metadata
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

    return {"status": "uploaded", "url": f"/videos/{game_id}.mp4"}

@app.get("/api/games", response_model=List[GameSchema])
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).order_by(Game.date.desc()))
    return result.scalars().all()

@app.get("/api/games/{game_id}", response_model=GameSchema)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    # Needed to fetch relations async? Or rely on lazy load failing?
    # Async requires explicit load options usually, but for simple get it might work if schema doesn't force relation.
    # Schema includes events. We need select output with joinedload.
    
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Game).options(selectinload(Game.events)).where(Game.id == game_id)
    )
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
