import asyncio
from soccer_platform.database import AsyncSessionLocal
from soccer_platform.models import Game, Team, User
from sqlalchemy import select

async def debug_data():
    async with AsyncSessionLocal() as db:
        print("--- DEBUG: GAME DATA ---")
        # Get one game with teamsnap_data
        result = await db.execute(select(Game).where(Game.teamsnap_data.is_not(None)))
        game = result.scalars().first()
        if game:
            print(f"Game ID: {game.id}")
            print(f"Keys in properties: {list(game.teamsnap_data.keys())}")
            print(f"Raw Data: {game.teamsnap_data}")
        else:
            print("No games with teamsnap_data found.")

        print("\n--- DEBUG: TEAM DATA ---")
        # Get one team (Note: we didn't explicitily add teamsnap_data to Team model yet? Let's check models.py)
        # We added it to User and Game, but maybe not Team? I recall adding it to Team in startup migration but checking model is good.
        # Actually User user.teamsnap_data is there.
        # Let's check Team model in memory.
        result = await db.execute(select(Team))
        team = result.scalars().first()
        if team and hasattr(team, 'teamsnap_data') and team.teamsnap_data:
             print(f"Team ID: {team.id}")
             print(f"Keys: {list(team.teamsnap_data.keys())}")
        else:
            print("No team data or column empty.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(debug_data())
