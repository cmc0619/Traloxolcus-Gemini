import logging
import os
import time
import requests
import shutil
from .config import settings

logger = logging.getLogger("UploadAgent")

upload_service = None # Placeholder to allow class def above without circular issues if needed, but handled by class instantiation at bottom. Actually simpler to replace the file content.

class UploadService:
    def __init__(self):
        self.queue = []
        self.status = "idle"
        self.current_file = None
        self.base_url = settings.PLATFORM_URL
        self.creds = (settings.PLATFORM_USER, settings.PLATFORM_PASS)
        self.token = None
        self.uploaded_files = set()
        
    def get_status(self):
        return {
            "status": self.status,
            "current_op": self.current_file,
            "queue": len(self.queue)
        }

    def login(self):
        try:
            url = f"{self.base_url}/token"
            data = {"username": self.creds[0], "password": self.creds[1]}
            # OAuth2 expects form-data
            resp = requests.post(url, data=data, timeout=10)
            resp.raise_for_status()
            self.token = resp.json()["access_token"]
            logger.info("Logged in to Platform successfully.")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def scan_for_uploadables(self):
        # We look for EVENTS (.jsonl) as the signal that processing is done.
        # We assume the VIDEO (.mp4) is also ready in the parent dir.
        events_dir = settings.EVENTS_DIR
        if not os.path.exists(events_dir): return
        
        # Files like {session_id}_events.jsonl
        files = [f for f in os.listdir(events_dir) if f.endswith(".jsonl") and not f.endswith(".uploaded")]
        
        for f in files:
            if f not in self.queue and f not in self.uploaded_files:
                self.queue.append(f)

    def upload_session(self, event_filename):
        self.status = "uploading"
        self.current_file = event_filename
        
        # Session ID: "session123_events.jsonl" -> "session123"
        session_id = event_filename.replace("_events.jsonl", "")
        
        # Paths
        event_path = os.path.join(settings.EVENTS_DIR, event_filename)
        video_filename = f"{session_id}_stitched.mp4"
        video_path = os.path.join(settings.PROCESSED_STORAGE_DIR, video_filename)
        
        if not os.path.exists(video_path):
            logger.warning(f"Video {video_path} missing for events {event_filename}. Skipping.")
            self.queue.remove(event_filename) # Maybe wait? But for now remove.
            return

        if not self.token:
            if not self.login():
                return # Retry next loop

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # 1. Create/Check Game Metadata
            logger.info(f"Creating Game {session_id}...")
            # We don't have date easily unless we parse filename. Let's send basic ID.
            resp = requests.post(
                f"{self.base_url}/api/games",
                json={"id": session_id, "status": "uploading"},
                headers=headers,
                timeout=10
            )
            if resp.status_code == 401:
                self.token = None # Refresh token next time
                raise Exception("Unauthorized - Token Expired")
            resp.raise_for_status()

            # 2. Upload Video
            logger.info(f"Uploading Video {video_filename}...")
            with open(video_path, 'rb') as f:
                resp = requests.post(
                    f"{self.base_url}/api/games/{session_id}/video",
                    files={"file": f},
                    headers=headers,
                    timeout=300 # 5 mins
                )
            resp.raise_for_status()

            # 3. Upload Events
            # Platform expects list of events. We need to parse JSONL.
            import json
            events = []
            with open(event_path, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
            
            logger.info(f"Uploading {len(events)} events...")
            resp = requests.post(
                f"{self.base_url}/api/games/{session_id}/events",
                json=events,
                headers=headers,
                timeout=30
            )
            resp.raise_for_status()

            # Success
            logger.info(f"Upload Complete for {session_id}")
            self.uploaded_files.add(event_filename)
            self.queue.remove(event_filename)
            
            # Mark uploaded
            os.rename(event_path, event_path + ".uploaded")
            
        except Exception as e:
            logger.error(f"Upload failed for {session_id}: {e}")
        finally:
            self.status = "idle"
            self.current_file = None

    def running_loop(self):
        logger.info("Starting Upload Loop...")
        # Initial Login
        self.login()
        
        while True:
            self.scan_for_uploadables()
            
            if self.queue:
                f = self.queue[0]
                self.upload_session(f)
            else:
                time.sleep(10)

upload_service = UploadService()
