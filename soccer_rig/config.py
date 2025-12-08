import os
import platform
import socket
import json
from typing import Any, Dict

class Settings:
    PROJECT_NAME: str = "Soccer Cam"
    VERSION: str = "1.3.0"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RECORDINGS_DIR: str = os.getenv("RECORDINGS_DIR", os.path.join(BASE_DIR, "recordings"))
    LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
    SETTINGS_FILE: str = os.path.join(BASE_DIR, "settings.json")
    
    # Hardware / Mode
    IS_PI: bool = platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
    IS_WINDOWS: bool = platform.system() == "Windows"
    DEV_MODE: bool = os.getenv("DEV_MODE", "True").lower() == "true"
    
    def __init__(self):
        # Defaults
        self.NODE_ID: str = socket.gethostname()
        self.DEFAULT_WIDTH: int = 3840
        self.DEFAULT_HEIGHT: int = 2160
        self.DEFAULT_FPS: int = 30
        self.DEFAULT_BITRATE: int = 30000000
        self.HOST: str = "0.0.0.0"
        self.PORT: int = 8000
        
        # Load from file
        self.load()

    def load(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.NODE_ID = data.get("node_id", self.NODE_ID)
                    self.DEFAULT_WIDTH = data.get("width", self.DEFAULT_WIDTH)
                    self.DEFAULT_HEIGHT = data.get("height", self.DEFAULT_HEIGHT)
                    self.DEFAULT_FPS = data.get("fps", self.DEFAULT_FPS)
                    self.DEFAULT_BITRATE = data.get("bitrate", self.DEFAULT_BITRATE)
                    # Host/Port usually env var controlled for startup, but could be here too
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save(self, data: Dict[str, Any]):
        try:
            # Update local
            self.NODE_ID = data.get("node_id", self.NODE_ID)
            self.DEFAULT_WIDTH = int(data.get("width", self.DEFAULT_WIDTH))
            self.DEFAULT_HEIGHT = int(data.get("height", self.DEFAULT_HEIGHT))
            self.DEFAULT_FPS = int(data.get("fps", self.DEFAULT_FPS))
            self.DEFAULT_BITRATE = int(data.get("bitrate", self.DEFAULT_BITRATE))
            
            # Write to file
            export_data = {
                "node_id": self.NODE_ID,
                "width": self.DEFAULT_WIDTH,
                "height": self.DEFAULT_HEIGHT,
                "fps": self.DEFAULT_FPS,
                "bitrate": self.DEFAULT_BITRATE
            }
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
            
    def to_dict(self):
         return {
            "node_id": self.NODE_ID,
            "width": self.DEFAULT_WIDTH,
            "height": self.DEFAULT_HEIGHT,
            "fps": self.DEFAULT_FPS,
            "bitrate": self.DEFAULT_BITRATE
         }

settings = Settings()

# Ensure directories exist
os.makedirs(settings.RECORDINGS_DIR, exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)
