import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Load Env
load_dotenv()

async def upgrade():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return

    # Convert sqlalchemy url to asyncpg url if needed (usually postgresql+asyncpg:// -> postgresql://)
    # But asyncpg needs just postgres:// usually or we parse it
    # Simplified: Assuming standard postgres connection string. 
    # If it is 'postgresql+asyncpg://user:pass@host/db', we strip '+asyncpg'
    
    dsn = db_url.replace("+asyncpg", "")
    
    print("Connecting to Database...")
    
    conn = None
    try:
        conn = await asyncpg.connect(dsn)
        
        # Add Columns to Users
        print("Adding teamsnap_refresh_token to users...")
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_refresh_token VARCHAR;")
        except Exception as e:
            print(f"Error adding refresh_token: {e}")

        print("Adding teamsnap_token_expires_at to users...")
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS teamsnap_token_expires_at TIMESTAMP WITH TIME ZONE;") 
        except Exception as e:
            print(f"Error adding expires_at: {e}")
            
        print("Upgrade complete.")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(upgrade())
