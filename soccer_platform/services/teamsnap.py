import requests
import httpx
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
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, params=params, timeout=15)
            
            print(f"DEBUG: TeamSnap Response Status: {resp.status_code}")
            print(f"DEBUG: TeamSnap Response Headers: {resp.headers}")
            print(f"DEBUG: TeamSnap Response Body: {resp.text}")
            
            print(f"DEBUG: TeamSnap Response Body: {resp.text}")
            
            if resp.is_error:
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

    async def sync_teams_and_members(self, db: AsyncSession, ts_client=None):
        # 0. Resolve Token if client not provided
        from ..models import SystemSetting, Team
        from .libs.TeamSnappier import TeamSnappier
        
        ts = ts_client
        if not ts:
            token_setting = await db.execute(select(SystemSetting).where(SystemSetting.key == "TEAMSNAP_TOKEN"))
            token_setting = token_setting.scalars().first()
            token = token_setting.value if token_setting else settings.TEAMSNAP_TOKEN

            if not token:
                return {"status": "error", "message": "No TeamSnap token configured."}

            # 1. Init Client
            ts = TeamSnappier(auth_token=token)
        
        try:
            # 2. Get User & Teams
            # TeamSnappier uses find_me() and returns a list of flattened dicts
            me_list = ts.find_me()
            
            if not me_list:
                 return {"status": "error", "message": "TeamSnap find_me() failed or returned empty."}

            # find_me returns list of dicts
            user_id = me_list[0]['id']
            
            teams = ts.list_teams(user_id)
            if not teams:
                 return {"status": "ok", "message": "No teams found for user.", "stats": {"users_created": 0, "teams_synced": 0}}
            
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
                        age_group=team_data.get('division_name'),
                        birth_year=None,
                        teamsnap_data=team_data # RAW DATA
                    )
                    db.add(team_obj)
                    await db.flush() 
                    sync_stats['teams_synced'] += 1
                else: 
                     # Update raw data if exists
                     team_obj.teamsnap_data = team_data
                     # Update other fields if changed? 
                     # For now, just raw data is critical for "store everything"
                     pass
                
                # 3. Get Roster
                members = ts.list_members(ts_team_id)
                if not members:
                    print(f"Warning: No members found or API failed for team {ts_team_id}")
                    continue

                # TeamSnappier returns list of flattened dicts
                
                for m_item in members:
                    m_attrs = m_item # Already flattened
                    
                    # DEBUG: Print first member to see structure
                    if sync_stats['users_created'] == 0 and sync_stats.get('debug_printed_member') is None:
                         print(f"DEBUG: Member Keys: {list(m_attrs.keys())}")
                         print(f"DEBUG: Member Data: {m_attrs}")
                         sync_stats['debug_printed_member'] = True

                    email = m_attrs.get('email') 
                    if not email:
                        email = m_attrs.get('email_address')
                    if not email:
                         # 'email_addresses' is often a list of dicts in raw API, 
                         # but TeamSnappier might have flattened it or kept it as list.
                         # Based on TeamSnappier.py print_members: "Email address: {member['email_addresses']}"
                         # It seems it might be a list or string.
                         e_addrs = m_attrs.get('email_addresses')
                         if e_addrs:
                             if isinstance(e_addrs, list) and len(e_addrs) > 0:
                                 # If it's a list of dicts, try to find 'value' or just use first item if it's string
                                 item = e_addrs[0]
                                 if isinstance(item, dict):
                                     email = item.get('value') or item.get('email')
                                 else:
                                     email = str(item)
                             else:
                                 email = str(e_addrs)

                    if not email:
                        # Last ditch: Look for any key with 'email' in it
                        for k, v in m_attrs.items():
                            if 'email' in k and v:
                                email = str(v)
                                break
                    
                    if not email:
                        print(f"DEBUG: Skipping member {m_attrs.get('first_name')} - No Email found.")
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
                            role="coach" if m_attrs.get('is_owner') else "parent", # Default to parent
                            full_name=full_name,
                            nickname=m_attrs.get('nickname'),
                            teamsnap_data=m_attrs # RAW DATA
                        )
                        db.add(user)
                        await db.flush() # Get ID
                        
                        # Create Association
                        from ..models import UserTeam
                        association = UserTeam(
                            user_id=user.id,
                            team_id=team_obj.id,
                            jersey_number=int(jersey) if jersey and str(jersey).isdigit() else None
                        )
                        db.add(association)
                        sync_stats['users_created'] += 1
                    else:
                        # Update raw user data
                        user.teamsnap_data = m_attrs
                        user.nickname = m_attrs.get('nickname') # Update nickname too if changed
                        # Ensure association exists
                        from ..models import UserTeam
                        res = await db.execute(select(UserTeam).where(
                            (UserTeam.user_id == user.id) & (UserTeam.team_id == team_obj.id)
                        ))
                        assoc = res.scalars().first()
                        
                        jersey = m_attrs.get('jersey_number')
                        jersey_val = int(jersey) if jersey and str(jersey).isdigit() else None
                        
                        if not assoc:
                            assoc = UserTeam(
                                user_id=user.id,
                                team_id=team_obj.id,
                                jersey_number=jersey_val
                            )
                            db.add(assoc)
                        else:
                            # Update Jersey if changed
                            if jersey_val is not None:
                                assoc.jersey_number = jersey_val
            
            await db.commit()
            return {"status": "ok", "stats": sync_stats}

        except Exception as e:
            return {"status": "error", "message": f"Sync failed: {str(e)}"}

    async def sync_schedule(self, db: AsyncSession, ts_client=None):
        from ..models import SystemSetting, Team, Game
        from .libs.TeamSnappier import TeamSnappier
        import uuid
        from dateutil import parser # Assuming dateutil is available or use datetime
        from datetime import datetime
        
        ts = ts_client
        if not ts:
            token_setting = await db.execute(select(SystemSetting).where(SystemSetting.key == "TEAMSNAP_TOKEN"))
            token_setting = token_setting.scalars().first()
            token = token_setting.value if token_setting else settings.TEAMSNAP_TOKEN
            if not token: return {"status": "error", "message": "No Token"}
            ts = TeamSnappier(auth_token=token)
            
        stats = {"games_synced": 0, "games_created": 0}
        
        try:
             # Get all teams from DB to iterate
             res = await db.execute(select(Team))
             db_teams = res.scalars().all()
             
             for team in db_teams:
                 if not team.teamsnap_id: continue
                 
                 events = ts.list_events(teamid=team.teamsnap_id)
                 if not events: continue
                 
                 for ev in events:
                     # Filter for Games? TeamSnap events have 'is_game' usually? 
                     # Let's check keys if possible. raw data keys usually have 'is_game'.
                     # Assuming 'is_game' is present in flattened dict.
                     is_game = ev.get('is_game')
                     if is_game is False: continue # Skip practices for now if strict? Or store all?
                     # User wanted "Game/Schedule Sync". 
                     # Let's store all but mark them? Game model implies "Game".
                     # If I store practices in Game table, status might be confusing.
                     # Let's stick to is_game=True for Game table for now.
                     
                     if ev.get('is_game'):
                         ts_id = str(ev.get('id'))
                         
                         # Parse Date using native strptime if ISO or dateutil
                         # TeamSnap format: "2023-10-21T14:30:00+00:00"
                         dt_str = ev.get('start_date')
                         game_date = None
                         
                         # Check existing
                         res = await db.execute(select(Game).where(Game.teamsnap_id == ts_id))
                         game_obj = res.scalars().first()
                         
                         if dt_str:
                             try:
                                 game_date = parser.parse(dt_str)
                             except:
                                 pass
                         
                         if not game_obj:
                             game_obj = Game(
                                 id=str(uuid.uuid4()),
                                 teamsnap_id=ts_id,
                                 team_id=team.id,
                                 opponent=ev.get('opponent_name'),
                                 date=game_date,
                                 status="scheduled", # Default
                                 teamsnap_data=ev
                             )
                             db.add(game_obj)
                             stats['games_created'] += 1
                         else:
                             game_obj.teamsnap_data = ev
                             game_obj.date = game_date
                             game_obj.opponent = ev.get('opponent_name')
                             
                         stats['games_synced'] += 1
             
             await db.commit()
             return {"status": "ok", "stats": stats}
             
        except Exception as e:
            print(f"Schedule Sync Error: {e}")
            return {"status": "error", "message": str(e)}

    async def sync_full(self, db: AsyncSession):
        # Master sync
        from ..models import SystemSetting
        from .libs.TeamSnappier import TeamSnappier
        
        token_setting = await db.execute(select(SystemSetting).where(SystemSetting.key == "TEAMSNAP_TOKEN"))
        token_setting = token_setting.scalars().first()
        token = token_setting.value if token_setting else settings.TEAMSNAP_TOKEN
        
        if not token: return {"status": "error", "message": "No Token"}
        
        ts = TeamSnappier(auth_token=token)
        
        # 1. Teams & Members
        r1 = await self.sync_teams_and_members(db, ts_client=ts)
        
        # 2. Schedule
        r2 = await self.sync_schedule(db, ts_client=ts)
        
        return {
            "status": "ok", 
            "roster_stats": r1.get('stats', r1), 
            "schedule_stats": r2.get('stats', r2)
        }
        
    # Backward compatibility wrapper if needed, but we will update main.py
    async def sync_roster(self, db: AsyncSession):
        return await self.sync_full(db)

teamsnap_service = TeamSnapService()
