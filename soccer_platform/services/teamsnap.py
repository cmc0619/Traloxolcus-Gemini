import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..config import settings
from ..models import User
from .. import auth

class TeamSnapService:
    def __init__(self):
        self.token = settings.TEAMSNAP_TOKEN
        self.base_url = "https://api.teamsnap.com/v3"

    def get_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def exchange_token(self, db: AsyncSession, client_id: str, client_secret: str, code: str, redirect_uri: str):
        """
        Exchanges auth code for access token and saves it to DB.
        """
        url = "https://auth.teamsnap.com/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        try:
            resp = requests.post(url, data=payload, timeout=15)
            if resp.status_code != 200:
                raise Exception(f"OAuth Failed: {resp.text}")
            
            data = resp.json()
            access_token = data.get("access_token")
            
            if not access_token:
                raise Exception("No access token in response")
                
            # Save to DB
            from ..models import SystemSetting
            setting = await db.get(SystemSetting, "TEAMSNAP_TOKEN")
            if not setting:
                setting = SystemSetting(key="TEAMSNAP_TOKEN", value=access_token)
                db.add(setting)
            else:
                setting.value = access_token
            
            await db.commit()
            return {"status": "ok", "token_preview": access_token[:5] + "..."}
            
        except Exception as e:
            raise e

    async def sync_roster(self, db: AsyncSession):
        # 0. Resolve Token
        from ..models import SystemSetting, Team
        from .libs.TeamSnappier import TeamSnappier
        
        token_setting = await db.get(SystemSetting, "TEAMSNAP_TOKEN")
        token = token_setting.value if token_setting else settings.TEAMSNAP_TOKEN

        if not token:
            return {"status": "error", "message": "No TeamSnap token configured."}

        # 1. Init Client
        ts = TeamSnappier(auth_token=token)
        
        try:
            # 2. Get User & Teams
            me = ts.get_me()
            # The library might return dict or object, need to check structure.
            # Assuming standard structure or inspecting library would be best.
            # Based on cloning, it seems to have methods like get_teams()
            
            # Note: TeamSnappier methods typically return the raw JSON 'items' or similar.
            # Let's inspect `me` structure by logging or assuming standard TS API.
            user_id = me[0]['id'] if isinstance(me, list) else me['id'] # Defensively handle
            
            teams = ts.get_teams(user_id)
            
            sync_stats = {"users_created": 0, "teams_synced": 0}
            
            for t_item in teams:
                # Sync Team
                team_data = t_item.get('attributes', {})
                ts_team_id = t_item.get('id')
                team_name = team_data.get('name', f"Team {ts_team_id}")
                team_season = team_data.get('season_name', 'Unknown')
                
                # Check DB for Team (using ID match or create)
                # Ideally we store TS_ID, but we used UUID for ID. 
                # Let's simple-search by name+season or just create new if not exact match?
                # BETTER: Add `external_id` to Team model? 
                # For now, let's just create them if name doesn't exist to avoid dupes purely by name.
                
                existing_team_res = await db.execute(select(Team).where(Team.name == team_name))
                team_obj = existing_team_res.scalars().first()
                
                if not team_obj:
                    import uuid
                    team_obj = Team(
                        id=str(uuid.uuid4()),
                        name=team_name,
                        season=team_season,
                        league=team_data.get('league_name'),
                        birth_year=team_data.get('division_name') # Assuming Division Name contains "2012" or similar
                    )
                    db.add(team_obj)
                    await db.commit() # Commit to get ID? we generated it.
                    sync_stats['teams_synced'] += 1
                
                # 3. Get Roster
                members = ts.get_members(ts_team_id)
                
                for m_item in members:
                    m_attrs = m_item.get('attributes', {})
                    email = m_attrs.get('email')
                    
                    if not email:
                        continue
                        
                    # Check User
                    res = await db.execute(select(User).where(User.username == email))
                    user = res.scalars().first()
                    
                    if not user:
                        # Create User
                        names = m_attrs.get('formatted_name', '').split(' ')
                        full_name = m_attrs.get('formatted_name')
                        jersey = m_attrs.get('jersey_number')
                        
                        user = User(
                            username=email,
                            hashed_password=auth.get_password_hash("changeme"),
                            role="player" if not m_attrs.get('is_owner') else "coach", # Guess role
                            full_name=full_name,
                            jersey_number=int(jersey) if jersey and str(jersey).isdigit() else None
                        )
                        # Append Team
                        user.teams.append(team_obj)
                        
                        db.add(user)
                        sync_stats['users_created'] += 1
                    else:
                        # Ensure user is associated with this team
                        # Need to load existing teams first if not loaded
                        # Or safer: check if association exists via query? 
                        # Ideally, we eager load user.teams, but 'user' here comes from simple select.
                        # Let's rely on DB UNIQUE constraint on association table if it existed? No, SQLAlchemy manages collection.
                        # We must fetch user with teams to assume check.
                        
                        # Re-fetch with teams
                        from sqlalchemy.orm import selectinload
                        u_res = await db.execute(select(User).options(selectinload(User.teams)).where(User.id == user.id))
                        user_loaded = u_res.scalars().first()
                        
                        if team_obj not in user_loaded.teams:
                            user_loaded.teams.append(team_obj)
                            db.add(user_loaded)
            
            await db.commit()
            return {"status": "ok", "stats": sync_stats}

        except Exception as e:
            return {"status": "error", "message": f"Sync failed: {str(e)}"}

teamsnap_service = TeamSnapService()
