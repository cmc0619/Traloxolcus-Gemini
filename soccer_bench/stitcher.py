import os
import subprocess
import glob
import logging
from typing import Dict, List, Optional
from .config import settings

logger = logging.getLogger("Stitcher")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

class StitcherService:
    def __init__(self):
        self.raw_dir = settings.RAW_STORAGE_DIR
        self.output_dir = settings.OUTPUT_DIR
        ensure_dir(self.output_dir)

    def find_sessions(self) -> Dict[str, Dict[str, str]]:
        """
        Groups video files by Session ID.
        Returns: { "session_123": { "CAM_L": "path/to/L.mp4", "CAM_C": ... } }
        """
        # File pattern: {SESSION}_{CAM}_{DATE}_{TIME}.mp4
        # We need to parse this.
        # But wait, we also have manifests.
        # Let's rely on standard naming convention in Ingest.
        
        sessions = {}
        files = glob.glob(os.path.join(self.raw_dir, "*.mp4"))
        
        import re
        # Pattern: SessionID_CamID_Date_Time.mp4
        # Capture: (Session) (Cam) (Date) (Time)
        # We need to handle cases where SessionID has underscores.
        # We assume CamID is like CAM_L, CAM_C, CAM_R or CAM-L...
        # And Date is 8 digits, Time 6 digits at the end.
        
        pattern = re.compile(r"^(.*)_(CAM[_-]?[LCR])_(\d{8})_(\d{6})\.mp4$", re.IGNORECASE)

        for f_path in files:
            fname = os.path.basename(f_path)
            match = pattern.match(fname)
            
            if not match:
                logger.warning(f"File {fname} does not match naming convention. Skipping.")
                continue
                
            session_id = match.group(1)
            cam_raw = match.group(2).upper() # Normalize
            
            # Normalize Role
            if "L" in cam_raw: cam_role = "CAM_L"
            elif "C" in cam_raw: cam_role = "CAM_C"
            elif "R" in cam_raw: cam_role = "CAM_R"
            else: continue
            
            if session_id not in sessions:
                sessions[session_id] = {}
            
            sessions[session_id][cam_role] = f_path
            
        return sessions

    def stitch_session(self, session_id: str, cam_files: Dict[str, str]):
        """
        Runs FFMPEG to stitch files.
        """
        # Quality check: Need all 3?
        required = ["CAM_L", "CAM_C", "CAM_R"]
        missing = [param for param in required if param not in cam_files]
        if missing:
            logger.warning(f"Session {session_id} incomplete. Missing: {missing}. Skipping.")
            return

        outfile = os.path.join(self.output_dir, f"{session_id}_stitched.mp4")
        if os.path.exists(outfile):
            logger.info(f"Session {session_id} already stitched. Skipping.")
            return

        logger.info(f"Stitching Session: {session_id}")
        
        # Inputs
        input_args = []
        input_args.extend(["-i", cam_files["CAM_L"]])
        input_args.extend(["-i", cam_files["CAM_C"]])
        input_args.extend(["-i", cam_files["CAM_R"]])
        
        # Filter Complex: Horizontal Stack (MVP)
        # [0:v][1:v][2:v]hstack=inputs=3[v]
        filter_complex = "[0:v][1:v][2:v]hstack=inputs=3[v]"
        
        # Encoding Config (NVENC for speed)
        # -c:v hevc_nvenc -preset p4 -cq 20
        # If no GPU, fall back to libx265?
        # Let's assume NVENC as per README reqs.
        
        cmd = [
            "ffmpeg",
            "-y", # Overwrite
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-c:v", "hevc_nvenc", # NVIDIA H.265
            "-preset", "p4",
            "-b:v", "15M", # Adjust based on needs. 15M for stitched 12K width? Might need more.
            # Actually 3x 4K side-by-side is 11520x2160. That's huge.
            # Maybe scale down?
            # Let's scale to total width 4K (3840 wide).
            # 3840 / 3 = 1280 per cam.
            # filter: hstack=inputs=3,scale=3840:-1
            # "-filter_complex", "[0:v][1:v][2:v]hstack=inputs=3,scale=3840:-1[v]",
             outfile
        ]
        
        # Try full res first? 12K video is hard to play.
        # Let's do a sensible 4K panoramic output.
        cmd[7] = "[0:v][1:v][2:v]hstack=inputs=3,scale=3840:-1[v]"

        logger.info(f"Running ffmpeg: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Stitching valid for {session_id}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e}")
            return False

def run_stitcher():
    service = StitcherService()
    sessions = service.find_sessions()
    logger.info(f"Found {len(sessions)} sessions.")
    
    for sess_id, files in sessions.items():
        service.stitch_session(sess_id, files)

if __name__ == "__main__":
    run_stitcher()
