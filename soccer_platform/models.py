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
