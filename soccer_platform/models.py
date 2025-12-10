from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Index

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    timestamp = Column(Float)
    frame = Column(Integer)
    type = Column(String, index=True)
    event_metadata = Column(JSONB, default={})
    
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
    jersey_number = Column(Integer, nullable=True)
    
    # M2M Relationship
    teams = relationship("Team", secondary=user_teams, back_populates="members")

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True)
    teamsnap_id = Column(String, index=True, nullable=True) # Unique ID from TeamSnap
    name = Column(String, index=True)
    league = Column(String)
    season = Column(String) # e.g. "Fall 2024"
    birth_year = Column(String) # e.g. "2012"
    
    age_group = Column(String, nullable=True)
    
    
    members = relationship("User", secondary=user_teams, back_populates="teams")
    games = relationship("Game", back_populates="team")

class SystemSetting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)
