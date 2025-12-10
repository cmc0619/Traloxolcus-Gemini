from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base

# Association Table
class UserTeam(Base):
    __tablename__ = "user_teams"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)
    jersey_number = Column(Integer, nullable=True)

    user = relationship("User", back_populates="team_associations")
    team = relationship("Team", back_populates="member_associations")

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, index=True) # UUID
    teamsnap_id = Column(String, unique=True, nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    opponent = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_home = Column(Boolean, default=False)
    status = Column(String, default="processing")
    date = Column(DateTime(timezone=True), nullable=True)
    video_path = Column(String, nullable=True)
    teamsnap_data = Column(JSONB, nullable=True) # RAW DATA
    
    # Relationships
    team = relationship("Team", back_populates="games")
    events = relationship("Event", back_populates="game")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    timestamp = Column(Float)
    frame = Column(Integer)
    type = Column(String, index=True)
    event_metadata = Column(JSONB, default=dict)
    
    game = relationship("Game", back_populates="events")
    player = relationship("User")
    team = relationship("Team")

    # Add GIN index for fast JSON querying
    __table_args__ = (
        Index('ix_events_metadata_gin', event_metadata, postgresql_using='gin'),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="parent") # "admin", "coach", "parent"
    full_name = Column(String, nullable=True)
    nickname = Column(String, nullable=True) # New Field
    teamsnap_token = Column(String, nullable=True) # User-level Token
    teamsnap_data = Column(JSONB, nullable=True) # RAW DATA
    # jersey_number = Column(Integer, nullable=True) # DEPRECATED: User UserTeam.jersey_number
    
    # Association Relationship
    team_associations = relationship("UserTeam", back_populates="user")
    
    # Proxy for simple access (read-only mostly unless using association proxy)
    # We will rely on associations for data
    
class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True)
    teamsnap_id = Column(String, index=True, nullable=True) # Unique ID from TeamSnap
    name = Column(String, index=True)
    league = Column(String)
    season = Column(String) # e.g. "Fall 2024"
    birth_year = Column(String) # e.g. "2012"
    
    age_group = Column(String, nullable=True)
    teamsnap_data = Column(JSONB, nullable=True) # RAW DATA
    
    member_associations = relationship("UserTeam", back_populates="team")
    games = relationship("Game", back_populates="team")

class SystemSetting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)
