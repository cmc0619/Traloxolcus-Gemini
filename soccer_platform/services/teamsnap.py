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
        url = "https://auth.teamsnap.com/oauth/token"
        # TeamSnap example uses query params for the POST request
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        try:
            print(f"DEBUG: Exchanging token. Redirect: {redirect_uri}, Code len: {len(code)}")
            
            # Using params=params as per TeamSnap Python example
            print(f"DEBUG: Sending POST to {url}")
            print(f"DEBUG: Params: {params}") 
            resp = requests.post(url, params=params, timeout=15)
            
            print(f"DEBUG: TeamSnap Response Status: {resp.status_code}")
            print(f"DEBUG: TeamSnap Response Headers: {resp.headers}")
            print(f"DEBUG: TeamSnap Response Body: {resp.text}")
            
            if resp.status_code != 200:
                print(f"DEBUG: OAuth Error Body: {resp.text}")
                raise Exception(f"OAuth Failed ({resp.status_code}): {resp.text}")
            
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
            # TeamSnappier uses find_me() and returns a list of flattened dicts
            me_list = ts.find_me()
            # find_me returns list of dicts
            user_id = me_list[0]['id']
            
            teams = ts.list_teams(user_id)
            
            sync_stats = {"users_created": 0, "teams_synced": 0}
            
            for t_item in teams:
                # TeamSnappier returns flattened dict, not JSONAPI attributes
                # Keys are 'id', 'name', 'season_name', etc.
                team_data = t_item # It is already the data dict
                ts_team_id = team_data.get('id')
                team_name = team_data.get('name', f"Team {ts_team_id}")
                team_season = team_data.get('season_name', 'Unknown')
                
                # Check DB for Team
                # Prioritize lookup by TeamSnap ID (Unique)
                existing_team_res = await db.execute(select(Team).where(Team.teamsnap_id == str(ts_team_id)))
                team_obj = existing_team_res.scalars().first()
                
                # Fallback to Name check (Legacy or manual teams)
                if not team_obj:
                    existing_team_res = await db.execute(select(Team).where(Team.name == team_name))
                    team_obj = existing_team_res.scalars().first()
                
                if not team_obj:
                    import uuid
                    team_obj = Team(
                        id=str(uuid.uuid4()),
                        teamsnap_id=str(ts_team_id),
                        name=team_name,
                        season=team_season,
                        league=team_data.get('league_name'),
                        age_group=team_data.get('division_name'), # Was incorrectly mapping to birth_year
                        birth_year=None # TODO: Extract from name if possible (e.g. "2014 Strikers")
                    )
                    db.add(team_obj)
                    await db.commit() 
                    sync_stats['teams_synced'] += 1
                
                # 3. Get Roster
                members = ts.list_members(ts_team_id)
                # TeamSnappier returns list of flattened dicts
                
                for m_item in members:
                    m_attrs = m_item # Already flattened
                    email = m_attrs.get('email') # 'email' might be key, or 'email_address'? TeamSnappier.py print_members says 'email_addresses'
                    # Let's check print_members in TeamSnappier.py: "Email address: {member['email_addresses']}"
                    # But the loop fills keys from "name". 'email' is common. 'email_address'? 
                    # Use .get('email') or .get('email_address')
                    if not email:
                        email = m_attrs.get('email_address')
                    
                    if not email:
                        continue
                        
                    # Check User
                    res = await db.execute(select(User).where(User.username == email))
                    user = res.scalars().first()
                    
                    if not user:
                        # Create User
                        full_name = m_attrs.get('formatted_name') or f"{m_attrs.get('first_name')} {m_attrs.get('last_name')}"
                        jersey = m_attrs.get('jersey_number')
                        
                        user = User(
                            username=email,
                            hashed_password=auth.get_password_hash("changeme"),
                            role="player" if not m_attrs.get('is_owner') else "coach", 
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
