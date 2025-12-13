from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from .. import auth, models, schemas

router = APIRouter(tags=["auth"])

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(select(models.User).where(models.User.username == form_data.username))
    user = result.scalars().first()
    
    # Mitigate timing attack
    if user:
        valid_password = auth.verify_password(form_data.password, user.hashed_password)
    else:
        # Run comparison against dummy string to consume time
        auth.verify_password(form_data.password, "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWrn96pzwLOx/u11RHVbvm.J8zkd.u")
        valid_password = False

    if not user or not valid_password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
