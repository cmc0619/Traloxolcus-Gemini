from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EventCreate(BaseModel):
    timestamp: float
    frame: int
    type: str
    metadata: Optional[dict] = {}

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
