from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["frontend"])

def get_frontend_path(filename: str):
    return os.path.join(os.path.dirname(__file__), "..", "frontend", filename)

@router.get("/")
async def read_index():
    return FileResponse(get_frontend_path("index.html"))

@router.get("/game")
async def read_game_page():
    return FileResponse(get_frontend_path("game.html"))

@router.get("/teamsnap")
async def read_teamsnap_page():
    return FileResponse(get_frontend_path("teamsnap.html"))

@router.get("/login")
async def read_login_page():
    # Login is already /login in some places, good.
    return FileResponse(get_frontend_path("login.html"))

@router.get("/settings")
async def read_settings_page():
    return FileResponse(get_frontend_path("settings.html"))

@router.get("/admin")
async def read_admin_page():
    return FileResponse(get_frontend_path("admin.html"))

@router.get("/roster")
async def read_roster_matrix_page():
    return FileResponse(get_frontend_path("roster_matrix.html"))

@router.get("/games")
async def read_games_page():
    return FileResponse(get_frontend_path("games.html"))

# Backward compatibility / Direct file access (Optional, but good for safety)
@router.get("/{filename}.html")
async def read_html_file(filename: str):
    # Basic security check
    if filename in ["index", "game", "teamsnap", "login", "settings", "admin", "roster_matrix", "games"]:
        return FileResponse(get_frontend_path(f"{filename}.html"))
    return FileResponse(get_frontend_path("404.html")) # Or error
