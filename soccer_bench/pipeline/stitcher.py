import os
import time
import subprocess
import logging
from ..config import settings

logger = logging.getLogger("Stitcher")

class StitchingService:
    def __init__(self):
        self.queue = [] # List of session_ids
        self.active_job = None
        self.processed_sessions = set()
        
    def get_status(self):
        return {
            "queue_length": len(self.queue),
            "active_job": self.active_job
        }

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def scan_for_sessions(self):
        """
        Scans raw storage for complete sets of videos (L, C, R).
        Example naming: {session_id}_{cam_id}_{timestamp}.mp4
        We need to group by session_id.
        """
        raw_dir = settings.RAW_STORAGE_DIR
        processed_dir = settings.PROCESSED_STORAGE_DIR
        if not os.path.exists(raw_dir):
            return

        files = [f for f in os.listdir(raw_dir) if f.endswith(".mp4") and not f.endswith(".bad")]
        
        # Group by Session ID
        # Filename: session123_CAM_L_2023...mp4
        sessions = {}
        for f in files:
            parts = f.split("_")
            if len(parts) < 3: continue
            
            # parts[0] is usually session_id if we follow naming convention
            # But the spec said {SESSION_ID}_{CAM_ID}...
            # Let's assume session_id doesn't have underscores for safety, 
            # or we rely on the CAM_ID tag to split.
            
            # Robust split: find CAM_L, CAM_C, CAM_R index
            cam_role = None
            if "CAM_L" in f: cam_role = "CAM_L"
            elif "CAM_C" in f: cam_role = "CAM_C"
            elif "CAM_R" in f: cam_role = "CAM_R"
            
            if not cam_role: continue
            
            # Session ID is everything before the cam_role
            session_id = f.split(f"_{cam_role}")[0]
            
            if session_id not in sessions:
                sessions[session_id] = {}
            
            sessions[session_id][cam_role] = f

        # Check for completeness
        for sid, roles in sessions.items():
            if sid in self.processed_sessions: continue
            if sid in self.queue: continue
            
            if "CAM_L" in roles and "CAM_C" in roles and "CAM_R" in roles:
                # Check if output already exists (avoid re-stitching on restart)
                out_file = os.path.join(processed_dir, f"{sid}_stitched.mp4")
                if os.path.exists(out_file):
                    self.processed_sessions.add(sid)
                    continue
                    
                logger.info(f"Found complete session: {sid}. Queuing for stitch.")
                self.queue.append(sid)

    def run_stitch_job(self, session_id):
        self.active_job = session_id
        
        raw_dir = settings.RAW_STORAGE_DIR
        out_dir = settings.PROCESSED_STORAGE_DIR
        self.ensure_dir(out_dir)
        
        # Find files again (could cache them but safe to look up)
        # We need exact paths
        files = [f for f in os.listdir(raw_dir) if f.startswith(session_id) and f.endswith(".mp4")]
        
        f_left = next((f for f in files if "CAM_L" in f), None)
        f_center = next((f for f in files if "CAM_C" in f), None)
        f_right = next((f for f in files if "CAM_R" in f), None)
        
        if not (f_left and f_center and f_right):
            logger.error(f"Job {session_id} failed: Missing files unexpectedly.")
            self.active_job = None
            return

        out_path = os.path.join(out_dir, f"{session_id}_stitched.mp4")
        
        # Build Command
        # ffmpeg -i L -i C -i R -filter_complex hstack=inputs=3 output
        cmd = [
            "ffmpeg", "-y",
            "-i", os.path.join(raw_dir, f_left),
            "-i", os.path.join(raw_dir, f_center),
            "-i", os.path.join(raw_dir, f_right),
            "-filter_complex", "[0:v][1:v][2:v]hstack=inputs=3[v]",
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-g", "30", # Keyframe every 1s (assuming 30fps) for fast seeking
            "-movflags", "+faststart", # Move metadata to front for instant web playback
            out_path
        ]
        
        logger.info(f"Stitching {session_id}...")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Stitching Complete: {out_path}")
            self.processed_sessions.add(session_id)
        except subprocess.CalledProcessError as e:
            logger.error(f"Stitching failed for {session_id}: {e}")
        except FileNotFoundError:
             logger.error("FFmpeg not found! Is it installed?")
        finally:
            self.active_job = None

    def running_loop(self):
        logger.info("Starting Stitching Loop...")
        while True:
            self.scan_for_sessions()
            
            if self.queue:
                sid = self.queue.pop(0)
                self.run_stitch_job(sid)
            else:
                time.sleep(5)

stitcher_service = StitchingService()
