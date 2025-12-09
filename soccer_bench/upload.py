import logging
import os
import time
import requests
import shutil
from ..config import settings

logger = logging.getLogger("UploadAgent")

class UploadService:
    def __init__(self):
        self.queue = []
        self.status = "idle" # idle, uploading
        self.current_file = None
        self.platform_url = settings.PLATFORM_URL
        self.uploaded_files = set()
        
    def get_status(self):
        return {
            "status": self.status,
            "file": self.current_file,
            "queue_length": len(self.queue)
        }

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def scan_for_uploadables(self):
        events_dir = settings.EVENTS_DIR
        self.ensure_dir(events_dir)
        
        # Look for .jsonl files that haven't been marked uploaded
        files = [f for f in os.listdir(events_dir) if f.endswith(".jsonl") and not f.endswith(".uploaded")]
        
        for f in files:
            if f not in self.queue and f not in self.uploaded_files:
                self.queue.append(f)

    def upload_file(self, filename):
        self.status = "uploading"
        self.current_file = filename
        file_path = os.path.join(settings.EVENTS_DIR, filename)
        
        if not os.path.exists(file_path):
            self.queue.remove(filename)
            return

        logger.info(f"Uploading {filename} to {self.platform_url}...")
        
        # Determine Session ID from filename (session_events.jsonl)
        session_id = filename.replace("_events.jsonl", "")
        
        try:
            # Prepare payload (Multipart or JSON body? Let's send file for simplicity)
            with open(file_path, 'rb') as f:
                # Mocking the endpoint for now until Platform exists
                # url = f"{self.platform_url}/api/v1/sessions/{session_id}/events"
                # resp = requests.post(url, files={'file': f}, timeout=30)
                # resp.raise_for_status()
                
                time.sleep(1) # Simulate network delay
                logger.info(f"Upload Simulated Success for {filename}")
                
            # success
            self.uploaded_files.add(filename)
            self.queue.remove(filename)
            
            # Mark as uploaded so we don't retry immediately
            os.rename(file_path, file_path + ".uploaded")
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            # Keep in queue to retry later
        finally:
            self.status = "idle"
            self.current_file = None

    def running_loop(self):
        logger.info("Starting Upload Loop...")
        while True:
            self.scan_for_uploadables()
            
            if self.queue:
                f = self.queue[0]
                self.upload_file(f)
            else:
                time.sleep(10)

upload_service = UploadService()
