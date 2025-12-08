from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, index=True) # Session ID
    date = Column(DateTime, default=datetime.utcnow)
    video_path = Column(String) # Path or S3 URL to stitched video
    status = Column(String) # processing, ready
    
    events = relationship("Event", back_populates="game")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    timestamp = Column(Float) # Seconds from start
    frame = Column(Integer)
    type = Column(String) # player_detected, ball_detected, goal, etc.
    metadata = Column(JSON) # Extra data (coordinates, confidence)

    game = relationship("Game", back_populates="events")
