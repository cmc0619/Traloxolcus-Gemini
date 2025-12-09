import os
from pydantic import BaseModel
from typing import List

class BenchConfig(BaseModel):
    # List of Rig URLs to poll
    # In prod, we might auto-discover via mDNS "soccer-cam-*.local"
    NODES: List[str] = [
        "http://soccer-cam-l.local:8000",
        "http://soccer-cam-c.local:8000",
        "http://soccer-cam-r.local:8000",
        "http://127.0.0.1:8000" # For local testing
    ]
    
    
    # Destination for raw files
    RAW_STORAGE_DIR: str = os.path.expanduser("~/SoccerFootage/Injest")
    # Destination for stitched files
    PROCESSED_STORAGE_DIR: str = os.path.expanduser("~/SoccerFootage/Processed")
    OUTPUT_DIR: str = PROCESSED_STORAGE_DIR # Alias for legacy
    
    # Destination for ML Events
    EVENTS_DIR: str = os.path.join(PROCESSED_STORAGE_DIR, "events")
    
    # Validation
    VERIFY_CHECKSUMS: bool = True
    
    # Platform
    PLATFORM_URL: str = "http://localhost" # Logic assumes port 80 now
    PLATFORM_USER: str = "coach"
    PLATFORM_PASS: str = "soccer"

settings = BenchConfig()
