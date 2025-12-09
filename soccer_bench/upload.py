import os
import requests
import json
import logging
from typing import Optional
from .config import settings

logger = logging.getLogger("Upload")

class UploadService:
    def __init__(self):
        self.platform_url = settings.PLATFORM_URL
        self.processed_dir = settings.OUTPUT_DIR

    def upload_game(self, video_path: str):
        """
        Uploads the game video and events to the Platform.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return

        base_name = os.path.basename(video_path).replace("_stitched.mp4", "")
        # Parse session_id from filename?
        # Filename: {session_id}_stitched.mp4
        session_id = base_name
        
        # 1. Create Game in Platform
        logger.info(f"Creating Game {session_id} on Platform...")
        try:
            payload = {"id": session_id, "status": "uploading"}
            resp = requests.post(f"{self.platform_url}/api/games", json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to create game: {e}")
            return

        # 2. Upload Video
        # We upload the file to the Platform API
        logger.info(f"Uploading video file {video_path}...")
        try:
            with open(video_path, 'rb') as f:
                # Use a new endpoint /api/games/{id}/video
                files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
                # This requires an endpoint on the other side
                # For MVP, let's assume we implement it or stick to shared storage if simpler.
                # BUT user said "Send to VPS". So we must upload.
                u_resp = requests.post(f"{self.platform_url}/api/games/{session_id}/video", files=files)
                u_resp.raise_for_status()
                
            video_url = u_resp.json().get("url") # Expecting the server to return the relative URL
            logger.info(f"Video uploaded. URL: {video_url}")
            
        except Exception as e:
            logger.error(f"Failed to upload video file: {e}")
            return # Stop if video fails

        # 3. Upload Events
        event_log = video_path.replace("_stitched.mp4", "_events.jsonl")
        if os.path.exists(event_log):
            logger.info(f"Uploading events for {session_id}...")
            events = []
            try:
                with open(event_log, "r") as f:
                    for line in f:
                        data = json.loads(line)
                        # Map fields
                        # Local: {timestamp, frame, players, ball_detected}
                        # Remote EventCreate: {timestamp, frame, type, metadata}
                        
                        # Create 'player_count' event?
                        # Or specific events?
                        # Let's just create one generic "frame_analysis" event per line? Too many.
                        # Only upload interesting ones?
                        if data.get("ball_detected"):
                             events.append({
                                 "timestamp": data["timestamp"],
                                 "frame": data["frame"],
                                 "type": "ball_detected",
                                 "metadata": {"players": data["players"]}
                             })
                
                # Batch upload
                if events:
                    # chunk it
                    chunk_size = 100
                    for i in range(0, len(events), chunk_size):
                        chunk = events[i:i+chunk_size]
                        requests.post(f"{self.platform_url}/api/games/{session_id}/events", json=chunk)
                    logger.info(f"Uploaded {len(events)} events.")
            
            except Exception as e:
                logger.error(f"Failed to upload events: {e}")

def run_upload():
    import glob
    service = UploadService()
    videos = glob.glob(os.path.join(settings.OUTPUT_DIR, "*_stitched.mp4"))
    
    for v in videos:
        service.upload_game(v)
