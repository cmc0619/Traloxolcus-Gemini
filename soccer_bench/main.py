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

# ... (Logging) ...

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
        
        for t in self.threads:
            t.start()
            
    def stop(self):
        logger.info("Stopping Services...")
        self.running = False
            
    def run_ingest(self):
        ingest_service.running_loop()

    def run_stitcher(self):
        stitcher_service.running_loop()

# ... (Lifespan, App) ...

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "ingest": ingest_service.get_status(),
        "pipeline": stitcher_service.get_status(),
        "upload": "idle",
        "disk_free_gb": 500 # Mock
    }

if __name__ == "__main__":
    uvicorn.run("soccer_bench.main:app", host="0.0.0.0", port=8080, reload=True)
