import os
import asyncio
import subprocess
from datetime import datetime
from sqlalchemy.future import select
from ..models import Game, Event, User
from ..database import async_session
from .. import auth
import secrets
import string

async def seed_demo_data():
    """
    Generates a demo video and database entry if they don't exist.
    Also ensures a default admin user exists.
    """
    print("Checking for Demo Data...")
    
    # 0. Admin User Check
    async with async_session() as db:
        result = await db.execute(select(User).where(User.role == "admin"))
        if not result.scalars().first():
            print("No Admin User found. Creating default admin...")
            
            # Generate random password
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            hashed = auth.get_password_hash(password)
            new_admin = User(
                username="admin",
                hashed_password=hashed,
                role="admin",
                full_name="System Admin",
                jersey_number=99
            )
            db.add(new_admin)
            await db.commit()
            
            print("="*40)
            print(f"ADMIN CREATED")
            print(f"Username: admin")
            print(f"Password: {password}")
            print("="*40)
        else:
            print("Admin user exists.")

    # 1. Generate Video
    video_dir = os.path.join(os.path.dirname(__file__), "../../videos")
    if not os.path.exists(video_dir):
        os.makedirs(video_dir, exist_ok=True)
        
    demo_path = os.path.join(video_dir, "demo_match.mp4")
    
    if not os.path.exists(demo_path):
        print("Generating 30s Demo Video (testsrc)...")
        # FFmpeg command to generate test source
        # Using -y to overwrite, -t 30 for duration
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=30:size=1280x720:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=30",
            "-c:v", "libx264", "-c:a", "aac",
            demo_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Demo Video Generated.")
        except Exception as e:
            print(f"Failed to generate demo video: {e}")
            return # Cannot proceed without video

    # 2. Database entry
    async with async_session() as db:
        result = await db.execute(select(Game).where(Game.id == "demo_match"))
        if result.scalars().first():
            print("Demo Game already exists.")
            return

        print("Creating Demo Game in DB...")
        new_game = Game(
            id="demo_match",
            status="processed", # Ready to play
            date=datetime.now(),
            video_path="/videos/demo_match.mp4"
        )
        db.add(new_game)
        
        # 3. Add Dummy Events
        # 30fps * 30s = 900 frames
        import random
        
        # Stats every 10 frames
        for f in range(0, 900, 10):
            t = f / 30.0
            
            # Simulate ball moving in a circle
            import math
            cx, cy = 640, 360
            r = 200
            angle = t # radians
            bx = cx + r * math.cos(angle)
            by = cy + r * math.sin(angle)
            
            event = Event(
                game_id="demo_match",
                timestamp=t,
                frame=f,
                type="stats",
                event_metadata={
                    "players": random.randint(10, 22),
                    "ball_detected": True,
                    "ball_coords": {"x": bx, "y": by, "w": 20, "h": 20, "confidence": 0.95}
                }
            )
            db.add(event)
            
        # Add a "Goal" event at 15s
        db.add(Event(
            game_id="demo_match",
            timestamp=15.0,
            frame=450,
            type="goal",
            event_metadata={"team": "Home", "player": "Demo Player"}
        ))
        
        await db.commit()
        print("Demo Data Seeded Successfully.")
