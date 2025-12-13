from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import aiofiles
import os

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_current_user
from ..notifications import send_game_processed_notification

router = APIRouter(prefix="/api", tags=["games"])

# --- Helper ---
def get_video_path(filename: str):
    # ../../videos from here
    return os.path.join(os.path.dirname(__file__), "..", "..", "videos", filename)

@router.get("/games", response_model=List[schemas.GameSummary])
async def list_games(
    team_id: Optional[str] = None, 
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(models.Game).order_by(models.Game.date.desc())
    
    if current_user.role != "admin":
        subq = select(models.UserTeam.team_id).where(models.UserTeam.user_id == current_user.id)
        stmt = stmt.where(models.Game.team_id.in_(subq))

    if team_id:
        stmt = stmt.where(models.Game.team_id == team_id)
    if status:
        stmt = stmt.where(models.Game.status == status)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/games", response_model=schemas.GameSchema)
async def create_game(game: schemas.GameCreate, db: AsyncSession = Depends(get_db)):
    db_game = await db.get(models.Game, game.id)
    if db_game:
        return db_game
    
    new_game = models.Game(id=game.id, status=game.status, date=game.date)
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    return new_game

@router.get("/games/{game_id}", response_model=schemas.GameSchema)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Game).options(selectinload(models.Game.events)).where(models.Game.id == game_id)
    )
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.patch("/games/{game_id}", response_model=schemas.GameSchema)
async def update_game(
    game_id: str, 
    game_update: schemas.GameUpdate, 
    current_user: models.User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin" and current_user.role != "coach":
        raise HTTPException(status_code=403)
        
    game = await db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game_update.video_path is not None:
        game.video_path = game_update.video_path
        
    if game_update.status is not None:
        game.status = game_update.status
        
    await db.commit()
    await db.refresh(game)
    return game

@router.post("/games/{game_id}/match")
async def match_game_video(
    game_id: str, 
    body: schemas.GameUpdate, 
    current_user: models.User = Depends(get_current_user), 
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

@router.post("/games/{game_id}/video")
async def upload_game_video(game_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    videos_path = os.path.join(os.path.dirname(__file__), "..", "..", "videos")
    os.makedirs(videos_path, exist_ok=True)
    
    file_path = os.path.join(videos_path, f"{game_id}.mp4")
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024): 
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    db_game = await db.get(models.Game, game_id)
    if db_game:
        db_game.video_path = f"/videos/{game_id}.mp4"
        db_game.status = "processed"
        await db.commit()
        await db.refresh(db_game)

        # Trigger Email
        # We need to run this async or background? 
        # Ideally background task, but notifications.py is async.
        # We can just await it since it's not super heavy (DB lookup + SMTP).
        await send_game_processed_notification(db, game_id)

    return {"status": "uploaded", "url": f"/videos/{game_id}.mp4"}

@router.get("/games/{game_id}/social")
async def get_social_clip(game_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_game = await db.get(models.Game, game_id)
    if not db_game or not db_game.video_path:
        raise HTTPException(status_code=404, detail="Game or video not found")

    filename = os.path.basename(db_game.video_path)
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "videos") 
    abs_video_path = os.path.join(base_dir, filename)
    abs_output_path = abs_video_path.replace(".mp4", "_vertical.mp4")
    
    if os.path.exists(abs_output_path):
        return {"status": "ready", "url": db_game.video_path.replace(".mp4", "_vertical.mp4")}

    result = await db.execute(select(models.Event).where(models.Event.game_id == game_id))
    events = result.scalars().all()
    
    from ..services.social import generate_vertical_clip
    background_tasks.add_task(generate_vertical_clip, game_id, abs_video_path, events)
    
    return {"status": "processing", "message": "Vertical clip generation started."}

@router.post("/games/{game_id}/events")
async def add_events(game_id: str, events: List[schemas.EventCreate], db: AsyncSession = Depends(get_db)):
    db_game = await db.get(models.Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    for e in events:
        new_event = models.Event(
            game_id=game_id,
            timestamp=e.timestamp,
            frame=e.frame,
            type=e.type,
            event_metadata=e.event_metadata
        )
        db.add(new_event)
    
    await db.commit()
    return {"status": "added", "count": len(events)}

@router.get("/search")
async def search_events(q: str, db: AsyncSession = Depends(get_db)):
    if not q: return []
    
    query = select(models.Event).join(models.Game).where(models.Event.type.ilike(f"%{q}%")).order_by(models.Event.timestamp)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [{
        "game_id": e.game_id,
        "time": e.timestamp,
        "type": e.type,
        "desc": f"{e.type} at {int(e.timestamp)}s"
    } for e in events]
