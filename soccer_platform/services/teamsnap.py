from teamsnappier import TeamSnappier
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..config import settings
from ..models import User
from .. import auth

class TeamSnapService:
    def __init__(self):
        self.token = settings.TEAMSNAP_TOKEN
        self.client = None
        if self.token:
            self.client = TeamSnappier(self.token)

    async def sync_roster(self, db: AsyncSession):
        if not self.client:
            return {"status": "error", "message": "No TeamSnap token configured."}

        # 1. Get Teams
        teams = self.client.get_teams()
        if not teams:
            return {"status": "ok", "message": "No teams found."}

        sync_count = 0
        
        # 2. Iterate Teams and Roster
        for team in teams:
            roster = self.client.get_roster(team['id'])
            for member in roster:
                # Basic logic: 
                # Create a User if email exists, role='player'
                # or role='parent' if distinct.
                # For simplicity, we just sync "Players" as Users for now.
                
                email = member.get('email')
                if not email:
                    continue
                    
                # Check exist
                res = await db.execute(select(User).where(User.username == email))
                if res.scalars().first():
                    continue 
                    
                # Create User
                # Default password: "changeme" -> In prod send invite email
                new_user = User(
                    username=email,
                    hashed_password=auth.get_password_hash("changeme"),
                    role="player"
                )
                db.add(new_user)
                sync_count += 1
        
        await db.commit()
        return {"status": "ok", "synced_users": sync_count}

teamsnap_service = TeamSnapService()
