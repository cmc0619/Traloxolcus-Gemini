import asyncio
from sqlalchemy.future import select
from soccer_platform.database import AsyncSessionLocal
from soccer_platform.models import Game
import json

async def inspect_data():
    async with AsyncSessionLocal() as db:
        # Get a game with teamsnap_data
        result = await db.execute(select(Game).where(Game.teamsnap_data.isnot(None)).limit(1))
        game = result.scalars().first()
        
        if not game:
            print("No games with TeamSnap data found.")
            return
            
        print(f"Game ID: {game.id}")
        print(f"Opponent: {game.opponent}")
        print(f"Is Home (DB): {game.is_home}")
        print("-" * 20)
        print("TeamSnap Data Keys:")
        data = game.teamsnap_data
        if isinstance(data, str):
            data = json.loads(data)
            
        for k, v in data.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    asyncio.run(inspect_data())
