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
        from ..models import SystemSetting
        token_setting = await db.get(SystemSetting, "TEAMSNAP_TOKEN")
        token = token_setting.value if token_setting else settings.TEAMSNAP_TOKEN

        if not token:
            return {"status": "error", "message": "No TeamSnap token configured."}

        # 1. Get User to find their ID
        try:
            me_resp = requests.get(f"{self.base_url}/me", headers=self.get_headers(token), timeout=10)
            if me_resp.status_code != 200:
                return {"status": "error", "message": "Failed to fetch TeamSnap user."}
            user_id = me_resp.json().get("collection", {}).get("items", [])[0].get("id")
            
            # 2. Get Teams
            teams_resp = requests.get(f"{self.base_url}/teams/search?user_id={user_id}", headers=self.get_headers(token), timeout=10)
            teams_data = teams_resp.json().get("collection", {}).get("items", [])
            
            sync_count = 0
            
            for item in teams_data:
                team_id = item.get("id")
                # 3. Get Roster (Members)
                members_resp = requests.get(f"{self.base_url}/members/search?team_id={team_id}", headers=self.get_headers(token), timeout=10)
                members_data = members_resp.json().get("collection", {}).get("items", [])
                
                for m_item in members_data:
                    # Parse attributes
                    attrs = {d['name']: d['value'] for d in m_item.get('data', [])}
                    email = attrs.get('email')
                    
                    if not email:
                        continue
                        
                    # Check exist
                    res = await db.execute(select(User).where(User.username == email))
                    if res.scalars().first():
                        continue 
                        
                    # Create User
                    new_user = User(
                        username=email,
                        hashed_password=auth.get_password_hash("changeme"),
                        role="player"
                    )
                    db.add(new_user)
                    sync_count += 1
            
            await db.commit()
            return {"status": "ok", "synced_users": sync_count}

        except Exception as e:
            return {"status": "error", "message": str(e)}

teamsnap_service = TeamSnapService()
