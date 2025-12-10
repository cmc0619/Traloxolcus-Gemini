import logging
import os
import cv2
import json
from ultralytics import YOLO
from typing import List, Dict
from tqdm import tqdm
from .config import settings

logger = logging.getLogger("ML_Analysis")

class AnalysisService:
    def __init__(self):
        self.model_path = "yolov8m.pt" # Medium model for balance
        # Check if we have a custom soccer model, otherwise download standard
        self.model = YOLO(self.model_path) 
        self.output_dir = settings.OUTPUT_DIR

    def analyze_video(self, video_path: str):
        """
        Runs YOLOv8 on the video to detect players and ball.
        Generates a .jsonl event log.
        """
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return

        base_name = os.path.basename(video_path).replace(".mp4", "")
        log_path = os.path.join(self.output_dir, f"{base_name}_events.jsonl")
        
        if os.path.exists(log_path):
             logger.info(f"Analysis already exists for {base_name}. Skipping.")
             return

        logger.info(f"Starting Analysis on {base_name}...")
        
        # Open Video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # We don't need to analyze every single frame for search.
        # Analyzing every 10th frame (3 times a second) is enough for "Activity Search".
        skip_frames = 10 
        
        events = []
        
        with open(log_path, "w") as f, tqdm(total=total_frames) as bar:
            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % skip_frames == 0:
                    # Run Inference
                    # Classes: 0=person, 32=sports ball (COCO dataset)
                    results = self.model(frame, classes=[0, 32], verbose=False)
                    
                    # Parse results
                    players_count = 0
                    ball_detected = False
                    ball_coords = None
                    
                    for r in results:
                        for box in r.boxes:
                            cls = int(box.cls[0])
                            if cls == 0: # person
                                players_count += 1
                            elif cls == 32: # sports ball
                                ball_detected = True
                                # Extract coordinates (center_x, center_y, w, h) normalized? No, usually pixels.
                                # box.xywh returns tensor. Convert to list.
                                xywh = box.xywh[0].tolist() 
                                ball_coords = {"x": xywh[0], "y": xywh[1], "w": xywh[2], "h": xywh[3]}

                    # Convert to EventCreate Schema
                    event_data = {
                        "timestamp": frame_idx / fps,
                        "frame": frame_idx,
                        "type": "stats", # Generic type for periodic stats
                        "event_metadata": {
                            "players": players_count,
                            "ball_detected": ball_detected,
                            "ball_coords": ball_coords
                        }
                    }
                    
                    # Convert to JSON line
                    json_line = json.dumps(event_data)
                    f.write(json_line + "\n")
                    
                frame_idx += 1
                bar.update(1)

        cap.release()
        logger.info(f"Analysis Complete. Log saved to {log_path}")

def run_analysis():
    # Find all stitched videos
    import glob
    videos = glob.glob(os.path.join(settings.OUTPUT_DIR, "*_stitched.mp4"))
    
    service = AnalysisService()
    
    for v in videos:
        service.analyze_video(v)

if __name__ == "__main__":
    run_analysis()
