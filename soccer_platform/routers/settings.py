from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database import get_db, set_sql_debug
from .. import models, schemas
from ..dependencies import get_current_user
from ..services.teamsnap import teamsnap_service

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=List[schemas.SettingItem])
async def get_settings(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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

@router.post("")
async def update_settings(settings: List[schemas.SettingItem], current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    
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

@router.post("/teamsnap_exchange")
async def exchange_teamsnap(req: schemas.TeamSnapExchangeRequest, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        print(f"DEBUG: Exchange Request Received. ClientID: {req.client_id[:5]}..., RedirectURI: {req.redirect_uri}")
        res = await teamsnap_service.exchange_token(db, req.client_id, req.client_secret, req.code, req.redirect_uri, user=current_user)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
