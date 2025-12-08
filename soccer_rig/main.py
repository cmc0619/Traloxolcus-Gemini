import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings

# Setup Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEV_MODE else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Node ID: {settings.NODE_ID}, Is Pi: {settings.IS_PI}")
    
    # Initialize services here (Camera, Sync, etc.)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    # Cleanup services

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

from .api.routes import router as api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (UI)
# We will create the static directory next
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION, "mode": "dev" if settings.DEV_MODE else "prod"}
