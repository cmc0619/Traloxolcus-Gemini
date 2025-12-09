import uvicorn
import logging
import threading
import signal
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .ingest import ingest_service
from .pipeline.stitcher import stitcher_service
from .pipeline.ml import ml_service

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("SoccerBench")

# Global Service Handle
service_manager = None

class ServiceManager:
    """
    Manages background threads for Ingest, Stitching, and Analysis.
    """
    def __init__(self):
        self.running = False
        self.threads = []
        
    def start(self):
        logger.info("Starting Background Services...")
        self.running = True
        
        # Start Ingest
        t_ingest = threading.Thread(target=self.run_ingest, daemon=True)
        self.threads.append(t_ingest)
        
        # Start Stitcher
        t_stitch = threading.Thread(target=self.run_stitcher, daemon=True)
        self.threads.append(t_stitch)
        
        # Start ML
        t_ml = threading.Thread(target=self.run_ml, daemon=True)
        self.threads.append(t_ml)
        
        for t in self.threads:
            t.start()
            
    def stop(self):
        logger.info("Stopping Services...")
        self.running = False
        # Services stop when daemon threads die, or we could add stop events.
        # ingest_service.stop() 
            
    def run_ingest(self):
        ingest_service.running_loop()

    def run_stitcher(self):
        stitcher_service.running_loop()

    def run_ml(self):
        ml_service.running_loop()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global service_manager
    service_manager = ServiceManager()
    service_manager.start()
    yield
    # Shutdown
    service_manager.stop()

app = FastAPI(lifespan=lifespan)

# Static Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

# Ensure dashboard dirs exist
os.makedirs(os.path.join(DASHBOARD_DIR, "static"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(DASHBOARD_DIR, "static")), name="static")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "ingest": ingest_service.get_status(),
        "pipeline": {
            "stitcher": stitcher_service.get_status(),
            "ml": ml_service.get_status()
        },
        "upload": "idle",
        "disk_free_gb": 500 # Mock
    }

if __name__ == "__main__":
    uvicorn.run("soccer_bench.main:app", host="0.0.0.0", port=4420, reload=True)
