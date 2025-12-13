from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["frontend"])

def get_frontend_path(filename: str):
    return os.path.join(os.path.dirname(__file__), "..", "frontend", filename)

@router.get("/")
async def read_index():
    return FileResponse(get_frontend_path("index.html"))

@router.get("/game.html")
async def read_game_page():
    return FileResponse(get_frontend_path("game.html"))

@router.get("/teamsnap.html")
async def read_teamsnap_page():
    return FileResponse(get_frontend_path("teamsnap.html"))

@router.get("/login")
async def read_login_page():
    return FileResponse(get_frontend_path("login.html"))

@router.get("/settings.html")
async def read_settings_page():
    return FileResponse(get_frontend_path("settings.html"))

@router.get("/admin.html")
async def read_admin_page():
    return FileResponse(get_frontend_path("admin.html"))

@router.get("/roster_matrix.html")
async def read_roster_matrix_page():
    return FileResponse(get_frontend_path("roster_matrix.html"))

@router.get("/games.html")
async def read_games_page():
    return FileResponse(get_frontend_path("games.html"))
