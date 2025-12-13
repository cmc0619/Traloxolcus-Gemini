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
    team_id: Optional[str] = None

class GameUpdate(BaseModel):
    video_path: Optional[str] = None
    status: Optional[str] = None

class GameSchema(GameCreate):
    video_path: Optional[str]
    events: List[EventCreate] = []

    class Config:
        from_attributes = True

class GameSummary(GameCreate):
    team_id: Optional[str] = None
    opponent: Optional[str] = None
    location: Optional[str] = None
    is_home: bool = False
    teamsnap_data: Optional[dict] = None
    video_path: Optional[str]
    # events excluded for list view performance

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TeamAssignment(BaseModel):
    team_id: str
    jersey_number: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "parent"
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    # jersey_number: Optional[int] = None # Removed global jersey
    teams: List[TeamAssignment] = [] 

class TeamBase(BaseModel):
    name: str
    season: Optional[str] = None
    league: Optional[str] = None
    age_group: Optional[str] = None 
    birth_year: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: str
    jersey_number: Optional[int] = None # Added field for display

    class Config:
        from_attributes = True

    # Removed duplicate UserResponse and improper validation logic
    pass

class UserTeamSchema(BaseModel):
    team: TeamResponse
    jersey_number: Optional[int]

    class Config:
        from_attributes = True

# Update UserResponse to use the new schema
class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str]
    nickname: Optional[str] = None
    teams: List[UserTeamSchema] = [] # Changed structure

    class Config:
        from_attributes = True

# Resolve circular ref
UserResponse.model_rebuild()

class UserTeamsnapCredsUpdate(BaseModel):
    client_id: str
    client_secret: str
