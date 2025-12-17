import asyncio
from sqlalchemy.future import select
from soccer_platform.database import AsyncSessionLocal
from soccer_platform.models import Team, UserTeam, User
from sqlalchemy.orm import selectinload

async def cleanup_non_soccer():
    print("Starting Cleanup of Non-Soccer Teams (Sport ID != 2)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Find all teams with sport_id != 2
        # Note: JSONB query or manual iteration. Manual iteration is safer for complex structure verification.
        result = await db.execute(select(Team))
        all_teams = result.scalars().all()
        
        teams_to_delete = []
        for t in all_teams:
            # Check raw data
            if not t.teamsnap_data: continue
            
            sid = str(t.teamsnap_data.get('sport_id'))
            if sid != "2":
                teams_to_delete.append(t)
                
        print(f"Found {len(teams_to_delete)} non-soccer teams to delete.")
        
        deleted_teams = 0
        deleted_users = 0
        
        for t in teams_to_delete:
            print(f"Processing Team: {t.name} (Sport: {t.teamsnap_data.get('sport_name', 'Unknown')})")
            
            # 2. Find Users in this team
            # We need to see if they have other teams.
            # Get members
            res = await db.execute(select(UserTeam).where(UserTeam.team_id == t.id))
            assocs = res.scalars().all()
            
            for assoc in assocs:
                user_id = assoc.user_id
                
                # Delete Association
                await db.delete(assoc)
                
                # Check User's other teams
                res_other = await db.execute(select(UserTeam).where((UserTeam.user_id == user_id) & (UserTeam.team_id != t.id)))
                other_teams = res_other.scalars().all()
                
                if not other_teams:
                    # User is orphaned? Check if admin/coach that shouldn't be deleted?
                    # Safer: Check role?
                    # Fetch User
                    res_u = await db.execute(select(User).where(User.id == user_id))
                    user = res_u.scalars().first()
                    
                    if user and user.role != 'admin':
                         print(f"  -> Deleting orphaned user: {user.username} ({user.full_name})")
                         await db.delete(user)
                         deleted_users += 1
            
            # Delete Team
            await db.delete(t)
            deleted_teams += 1
            
        await db.commit()
        print("="*30)
        print(f"Cleanup Complete.")
        print(f"Teams Deleted: {deleted_teams}")
        print(f"Users Deleted: {deleted_users}")
        print("="*30)

if __name__ == "__main__":
    asyncio.run(cleanup_non_soccer())
