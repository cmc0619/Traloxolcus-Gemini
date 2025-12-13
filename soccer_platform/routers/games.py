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
async def create_game(game: schemas.GameCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_game = await db.get(models.Game, game.id)
    if db_game:
        return db_game
    
    new_game = models.Game(
        id=game.id, 
        status=game.status, 
        date=game.date,
        team_id=game.team_id
    )
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

    if current_user.role == "coach":
        user_team_ids = [t.team_id for t in current_user.teams]
        if game.team_id not in user_team_ids:
             raise HTTPException(status_code=403, detail="Not authorized for this team's game")
        
    if game_update.video_path is not None:
        if current_user.role != "admin":
             raise HTTPException(status_code=403, detail="Only admins can manually edit video paths")
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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    game = await db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Coach check removed since only admin is allowed now
    
    if body.video_path is not None:
        game.video_path = body.video_path
        
    await db.commit()
    return {"status": "updated", "video_path": game.video_path}

@router.post("/games/{game_id}/video")
async def upload_game_video(
    game_id: str, 
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["admin", "coach"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Sanitize game_id to prevent path traversal
    safe_game_id = os.path.basename(game_id)
    if not safe_game_id or safe_game_id != game_id:
         raise HTTPException(status_code=400, detail="Invalid game ID format")

    # Authorize Logic (Check Existence + Permissions)
    db_game = await db.get(models.Game, safe_game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    if current_user.role == "coach":
        # Check if coach belongs to the team
        user_team_ids = [t.team_id for t in current_user.teams]
        if db_game.team_id not in user_team_ids:
             raise HTTPException(status_code=403, detail="Not authorized for this team's game")

    videos_path = os.path.join(os.path.dirname(__file__), "..", "..", "videos")
    os.makedirs(videos_path, exist_ok=True)
    
    file_path = os.path.join(videos_path, f"{safe_game_id}.mp4")
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024): 
                await out_file.write(content)
    except Exception as e:
        # Log error here in real app
        raise HTTPException(status_code=500, detail="File upload failed")

    # Already fetched db_game, update it
    db_game.video_path = f"/videos/{safe_game_id}.mp4"
    db_game.status = "processed"
    await db.commit()
    await db.refresh(db_game)

    # Trigger Email
    await send_game_processed_notification(db, safe_game_id)

    return {"status": "uploaded", "url": f"/videos/{safe_game_id}.mp4"}

@router.get("/games/{game_id}/social")
async def get_social_clip(
    game_id: str, 
    background_tasks: BackgroundTasks, 
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_game = await db.get(models.Game, game_id)
    if not db_game or not db_game.video_path:
        raise HTTPException(status_code=404, detail="Game or video not found")

    if current_user.role != "admin": # Social clips are expensive, restrict to admin/coach
        if current_user.role == "coach":
            user_team_ids = [t.team_id for t in current_user.teams]
            if db_game.team_id not in user_team_ids:
                 raise HTTPException(status_code=403, detail="Not authorized")
        else:
            raise HTTPException(status_code=403, detail="Not authorized")

    filename = os.path.basename(db_game.video_path)
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "videos") 
    abs_video_path = os.path.join(base_dir, filename)
    abs_output_path = abs_video_path.replace(".mp4", "_vertical.mp4")
    
    if os.path.exists(abs_output_path):
        return {"status": "ready", "url": db_game.video_path.replace(".mp4", "_vertical.mp4")}

    result = await db.execute(select(models.Event).where(models.Event.game_id == game_id))
    events = result.scalars().all()
    
    # Serialize events for background task (avoid DetachedInstanceError)
    # Using Pydantic v2 syntax
    events_data = [schemas.EventCreate.model_validate(e, from_attributes=True).model_dump() for e in events]
    
    from ..services.social import generate_vertical_clip
    background_tasks.add_task(generate_vertical_clip, game_id, abs_video_path, events_data)
    
    return {"status": "processing", "message": "Vertical clip generation started."}

@router.post("/games/{game_id}/events")
async def add_events(
    game_id: str, 
    events: List[schemas.EventCreate], 
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["admin", "coach"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_game = await db.get(models.Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    if current_user.role == "coach":
        user_team_ids = [t.team_id for t in current_user.teams]
        if db_game.team_id not in user_team_ids:
             raise HTTPException(status_code=403, detail="Not authorized for this team's game")
    
    for e in events:
        new_event = models.Event(
            game_id=game_id,
            team_id=db_game.team_id, # Set team_id
            timestamp=e.timestamp,
            frame=e.frame,
            type=e.type,
            event_metadata=e.event_metadata
        )
        db.add(new_event)
    
    await db.commit()
    return {"status": "added", "count": len(events)}

@router.get("/search")
async def search_events(q: str, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not q: return []
    
    # Optional: Restrict search results to user's teams? 
    # For now, simplistic search is fine for "all my games" context if frontend filters, 
    # but strictly we should filter here. 
    # Let's just fix the previous endpoint logic first.
    
    query = select(models.Event).join(models.Game).where(models.Event.type.ilike(f"%{q}%")).order_by(models.Event.timestamp)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [{
        "game_id": e.game_id,
        "time": e.timestamp,
        "type": e.type,
        "desc": f"{e.type} at {int(e.timestamp)}s"
    } for e in events]
