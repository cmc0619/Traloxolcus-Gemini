import logging
import os
import cv2
import json
import time
from ultralytics import YOLO
from tqdm import tqdm
from ..config import settings

logger = logging.getLogger("ML_Analysis")

class MLService:
    def __init__(self):
        self.model_path = "yolov8m.pt"
        self.model = None
        self.status = "idle" # idle, loading_model, analyzing
        self.current_file = None
        self.progress = 0
        self.fps_processing = 0
        self.stats = {"players": 0, "ball": False}
        
    def get_status(self):
        return {
            "status": self.status,
            "file": self.current_file,
            "progress": self.progress,
            "fps": self.fps_processing,
            "stats": self.stats
        }

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def load_model(self):
        if not self.model:
            self.status = "loading_model"
            logger.info(f"Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)

    def scan_and_process(self):
        in_dir = settings.PROCESSED_STORAGE_DIR
        out_dir = settings.EVENTS_DIR
        self.ensure_dir(out_dir)
        
        if not os.path.exists(in_dir): return

        # Find stitched videos
        files = [f for f in os.listdir(in_dir) if f.endswith("_stitched.mp4")]
        
        for vid_file in files:
            base_name = vid_file.replace(".mp4", "")
            event_file = os.path.join(out_dir, f"{base_name}_events.jsonl")
            
            if os.path.exists(event_file):
                continue # Already analyzed
                
            self.analyze_video(os.path.join(in_dir, vid_file), event_file)

    def analyze_video(self, video_path, output_path):
        self.load_model()
        self.status = "analyzing"
        self.current_file = os.path.basename(video_path)
        logger.info(f"Starting Analysis on {self.current_file}...")
        
        cap = cv2.VideoCapture(video_path)
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Analyze every 10th frame (3fps effective analysis)
        skip_frames = 10 
        
        start_time = time.time()
        
        with open(output_path, "w") as f:
            frame_idx = 0
            processed_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                if frame_idx % skip_frames == 0:
                    # Run Inference
                    results = self.model(frame, classes=[0, 32], verbose=False)
                    
                    frame_detections = {
                        "timestamp": frame_idx / fps_video,
                        "frame": frame_idx,
                        "players": 0,
                        "ball_detected": False
                    }
                    
                    for r in results:
                        for box in r.boxes:
                            cls = int(box.cls[0])
                            if cls == 0: frame_detections["players"] += 1
                            elif cls == 32: frame_detections["ball_detected"] = True
                            
                    # Write to log
                    f.write(json.dumps(frame_detections) + "\n")
                    
                    # Update Status
                    self.stats = {
                        "players": frame_detections["players"], 
                        "ball": frame_detections["ball_detected"]
                    }
                    
                    processed_count += 1
                    
                    # Calc status metrics
                    elapsed = time.time() - start_time
                    if elapsed > 1.0:
                        self.fps_processing = round(processed_count / elapsed, 1)
                
                self.progress = int((frame_idx / total_frames) * 100)
                frame_idx += 1
                
        cap.release()
        logger.info(f"Analysis Complete: {output_path}")
        self.status = "idle"
        self.current_file = None
        self.progress = 0

    def running_loop(self):
        logger.info("Starting ML Loop...")
        while True:
            try:
                self.scan_and_process()
            except Exception as e:
                logger.error(f"ML Loop error: {e}")
            time.sleep(5)

ml_service = MLService()
