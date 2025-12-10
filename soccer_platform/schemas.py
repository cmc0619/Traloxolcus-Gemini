from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EventCreate(BaseModel):
    timestamp: float
    frame: int
    type: str
    event_metadata: Optional[dict] = {}

class GameCreate(BaseModel):
    id: str # Session ID
    date: Optional[datetime] = None
    status: str = "processing"

class GameUpdate(BaseModel):
    video_path: Optional[str] = None
    status: Optional[str] = None

class GameSchema(GameCreate):
    video_path: Optional[str]
    events: List[EventCreate] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "parent"
    full_name: Optional[str] = None
    jersey_number: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str]
    jersey_number: Optional[int]
    class Config:
        from_attributes = True
