from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from .database import engine, Base, get_db
from .models import Game, Event
from .schemas import GameCreate, GameUpdate, EventCreate, GameSchema

app = FastAPI(title="Soccer Platform API")

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
