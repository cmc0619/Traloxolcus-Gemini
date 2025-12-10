from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EventCreate(BaseModel):
    timestamp: float
    frame: int
    type: str
    event_metadata: Optional[dict] = {}


class TeamSnapExchangeRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str

class SettingItem(BaseModel):
    key: str
    value: str

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

class GameSummary(GameCreate):
    video_path: Optional[str]
    # events excluded for list view performance

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "parent"
    full_name: Optional[str] = None
    jersey_number: Optional[int] = None
    team_ids: List[str] = [] # Changed from single team_id

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str]
    jersey_number: Optional[int]
    teams: List['TeamResponse'] = [] # M2M

    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: Optional[str] = "Unknown Team"
    birth_year: Optional[str] = None
    season: Optional[str] = None
    league: Optional[str] = None
    teamsnap_id: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: str
    class Config:
        from_attributes = True

# Resolve circular ref
UserResponse.model_rebuild()
