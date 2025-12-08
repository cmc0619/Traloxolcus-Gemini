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

        # 2. Upload Video (Mock or S3 presigned?)
        # For this MVP, we'll assume the Platform accepts a direct file path IF sharing storage (e.g. Volume),
        # OR we need a file upload endpoint.
        # The Platform API `GameUpdate` takes `video_path`.
        # If running in Docker with shared volume, we might just update the path?
        # But User requested "Upload to VPS".
        # Real Impl: Upload to S3, get URL.
        # MVP Impl: Just update the metadata and assume video is manually moved or use S3 later.
        # Let's add a todo log for S3.
        logger.info(f"(TODO) Uploading {video_path} to S3 bucket...")
        s3_url = f"s3://soccer-bucket/{os.path.basename(video_path)}" 
        
        # Update Game with Video URL
        try:
            patch = {"video_path": s3_url, "status": "processed"}
            requests.patch(f"{self.platform_url}/api/games/{session_id}", json=patch)
        except Exception as e:
            logger.error(f"Failed to update game status: {e}")

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
