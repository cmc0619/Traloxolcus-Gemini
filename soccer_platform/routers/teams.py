from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_current_user, get_current_admin_user
from ..services.teamsnap import teamsnap_service

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.post("", response_model=schemas.TeamResponse)
async def create_team(team: schemas.TeamCreate, current_user: models.User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    
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

@router.get("", response_model=List[schemas.TeamResponse])
async def list_teams(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Team))
    return result.scalars().all()

@router.post("/sync")
async def sync_teamsnap(current_user: models.User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):

    result = await teamsnap_service.sync_full(db)
    
    # If the service returns a response with its own status (e.g., an error),
    # return it directly to avoid masking the failure.
    if isinstance(result, dict) and "status" in result:
        return result
        
    return {"status": "ok", "stats": result}
