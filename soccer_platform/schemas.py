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

class TeamResponse(TeamBase):
    id: str
    jersey_number: Optional[int] = None # Added field for display

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: Optional[str]
    # jersey_number: Optional[int] # Deprecated on user
    teams: List[TeamResponse] = [] 

    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Custom logic to map association jersey numbers onto the team objects for the response
        # Since standard Pydantic from_attributes might not handle the complex association attributes easily 
        # when we want to flatten them into the TeamResponse.
        
        # However, SQLAlchemy models with from_attributes=True usually map properties.
        # But 'obj' here is the User model. obj.teams is gone/proxied.
        # We loaded 'team_associations'.
        
        # Let's verify if we can rely on Pydantic's automatic recursive validation if we structure it right.
        # But we want 'jersey_number' inside 'TeamResponse'.
        # The 'Team' model doesn't have jersey_number. The 'UserTeam' model does.
        
        # So we should probably construct the list of teams manually helper method or property on User model suitable for Pydantic?
        # Or, update UserResponse to return list of `UserTeamResponse` which contains `Team` and `Jersey`.
        # That changes the API contract structure slightly: teams: [{team: {...}, jersey: 10}]
        # BUT the user wants "Jersey #s should be more team/player centric".
        
        # Let's change the response structure to be cleaner:
        # UserResponse.teams -> List[UserTeamSchema]
        return super().model_validate(obj, **kwargs)

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
    teams: List[UserTeamSchema] = [] # Changed structure

    class Config:
        from_attributes = True

# Resolve circular ref
UserResponse.model_rebuild()
