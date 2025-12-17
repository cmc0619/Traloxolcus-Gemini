from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from .. import auth, models, schemas
from ..dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api", tags=["users"])

@router.post("/users", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, current_user: models.User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
        
    # Check existing
    res = await db.execute(select(models.User).where(models.User.username == user.username))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Username taken")
        
    hashed = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        hashed_password=hashed,
        role=user.role,
        full_name=user.full_name
        # jersey_number removed from User model
    )
    
    # Handle M2M Teams
    if user.teams:
        # Fetch teams to ensure they exist/valid
        requested_team_ids = [t.team_id for t in user.teams]
        teams_res = await db.execute(select(models.Team).where(models.Team.id.in_(requested_team_ids)))
        found_teams = {t.id: t for t in teams_res.scalars().all()}
        
        for assignment in user.teams:
            team_obj = found_teams.get(assignment.team_id)
            if team_obj:
                assoc = models.UserTeam(
                    user=new_user, 
                    team=team_obj, 
                    jersey_number=assignment.jersey_number
                )
                db.add(assoc)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Eager load teams for response
    stmt = select(models.User).options(selectinload(models.User.teams)).where(models.User.id == new_user.id)
    result = await db.execute(stmt)
    return result.scalars().first()

@router.get("/users/me", response_model=schemas.UserResponse)
async def get_my_user(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Re-fetch with eager loading for teams
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.teams).selectinload(models.UserTeam.team))
        .where(models.User.id == current_user.id)
    )
    user = result.scalars().first()
    
    # Construct response format manual mapping due to property fields if needed, 
    # but Pydantic from_attributes should handle 'teams' if structure matches
    # Schema expects: teams: List[UserTeamSchema], UserTeamSchema has team: TeamResponse
    # The relationship User.teams returns UserTeam objects, so it matches.
    return user

@router.get("/users", response_model=List[schemas.UserResponse])
async def list_users(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin" and 'coach' not in current_user.role:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Load associations then the team details
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.teams).selectinload(models.UserTeam.team))
    )
    users = result.scalars().all()
    
    resp = []
    for u in users:
        # Construct teams list from associations
        teams_data = []
        for assoc in u.teams:
            teams_data.append({
                "team": assoc.team,
                "jersey_number": assoc.jersey_number
            })
        
        resp.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "full_name": u.full_name,
            "nickname": u.nickname,
            "has_teamsnap_token": u.has_teamsnap_token,
            "teamsnap_token_expires_at": u.teamsnap_token_expires_at,
            "teams": teams_data
        })
    return resp

@router.put("/me/teamsnap_creds")
async def update_my_teamsnap_creds(creds: schemas.UserTeamsnapCredsUpdate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user:
         raise HTTPException(status_code=401)
    
    current_user.teamsnap_client_id = creds.client_id
    current_user.teamsnap_client_secret = creds.client_secret
    db.add(current_user)
    await db.commit()
    return {"status": "ok", "message": "Credentials updated"}
