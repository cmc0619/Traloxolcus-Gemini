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
    OUTPUT_DIR: str = os.path.expanduser("~/SoccerFootage/Processed")
    
    
    # Validation
    VERIFY_CHECKSUMS: bool = True
    
    # Platform
    PLATFORM_URL: str = "http://localhost:8080" # VPS URL

settings = BenchConfig()
