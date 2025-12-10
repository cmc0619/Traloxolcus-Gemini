from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, index=True) # UUID
    status = Column(String, default="processing")
    date = Column(DateTime(timezone=True), nullable=True)
    video_path = Column(String, nullable=True)
    
    events = relationship("Event", back_populates="game")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    timestamp = Column(Float)
    frame = Column(Integer)
    type = Column(String, index=True)
    event_metadata = Column(JSON, default={})
    
    game = relationship("Game", back_populates="events")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="parent") # "admin", "coach", "parent"
    full_name = Column(String, nullable=True)
    jersey_number = Column(Integer, nullable=True)

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True) # UUID or manually set
    name = Column(String)
    season = Column(String) # e.g. "2024-2025" or "Fall 2024"
    league = Column(String, nullable=True)
    age_group = Column(String, nullable=True) # e.g. "U12"

class SystemSetting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)
