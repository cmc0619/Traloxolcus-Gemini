import os
import logging
import numpy as np
from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx

logger = logging.getLogger("SocialExport")

def generate_vertical_clip(game_id: str, video_path: str, events: list):
    """
    Generates a 9:16 vertical crop of the game video, auto-following the ball.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return None

    output_path = video_path.replace(".mp4", "_vertical.mp4")
    
    # If already exists, return (simple cache)
    if os.path.exists(output_path):
        return output_path
        
    logger.info(f"Generating vertical clip for {game_id}...")
    
    try:
        clip = VideoFileClip(video_path)
        w, h = clip.size
        
        # Target Ratio 9:16
        target_ratio = 9/16
        # If we keep full height, what's the width?
        crop_w = int(h * target_ratio)
        crop_h = h
        
        # Build Trajectory
        # Events have {timestamp, metadata: {ball_coords: {x, y, ...}} }
        # We need a function x(t) that returns the center x for the crop.
        
        # 1. Extract ball centers
        # We'll create an array of (time, x_center)
        points = []
        for e in events:
            # Handle both Pydantic Models/ORM Objects AND Dicts
            if isinstance(e, dict):
                etype = e.get("type")
                emeta = e.get("event_metadata")
                etimestamp = e.get("timestamp", 0)
            else:
                etype = getattr(e, "type", None)
                emeta = getattr(e, "event_metadata", None)
                etimestamp = getattr(e, "timestamp", 0)

            if etype == "stats" and emeta and emeta.get("ball_coords"):
                bc = emeta["ball_coords"]
                # Ball center x
                bx = bc["x"] + (bc["w"] / 2)
                points.append((etimestamp, bx))
                
        # If no ball detection, just center crop
        if not points:
            logger.warning("No ball tracking data found. Defaulting to center crop.")
            final_clip = clip.fx(vfx.crop, x1=(w/2 - crop_w/2), width=crop_w, height=crop_h)
        else:
            # Sort by time
            points.sort(key=lambda p: p[0])
            times = np.array([p[0] for p in points])
            xs = np.array([p[1] for p in points])
            
            # Interpolate function
            def get_ball_x(t):
                # Find interpolation
                return np.interp(t, times, xs)

            # Smooth window (camera shouldn't jerk too much)
            # For simplicity in this v1, raw interpolation might be jerky. 
            # Ideally we'd smooth 'xs' before interp.
            # Let's do a simple moving average on xs if we have enough points
            if len(xs) > 10:
                window_size = 5
                xs_smooth = np.convolve(xs, np.ones(window_size)/window_size, mode='same')
            else:
                xs_smooth = xs

            def crop_get_params(t):
                # Determine x1
                bx = np.interp(t, times, xs_smooth)
                
                # Center the crop around bx
                x1 = bx - (crop_w / 2)
                
                # Clamp
                x1 = max(0, min(x1, w - crop_w))
                
                return x1

            # MoviePy's crop doesn't accept a function for x1 directly in standard FX?
            # actually clip.fx(vfx.crop, x1=...) accepts a function? 
            # Documentation says x1, y1 etc can be floats. 
            # For dynamic cropping, we use 'scroll' or complex crop.
            # Standard vfx.crop is static. 
            # We need to use fl(lambda gf, t: ...) which is complex.
            # OR simpler: use `clip.subclip(0, 60)` (limit to 1 min for performance)
            # and verify if crop supports dynamic. 
            # MoviePy v1.0.3 crop supports x_center=func(t).
            
            # Limit duration to 60s for Social Media (and performance)
            short_clip = clip.subclip(0, min(clip.duration, 60))
            
            final_clip = short_clip.crop(width=crop_w, height=crop_h, x_center=get_ball_x)

        # Write output
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        clip.close()
        final_clip.close()
        
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate clip: {e}")
        return None

def generate_widescreen_clip(game_id: str, video_path: str, events: list = None):
    """
    Generates a 16:9 widescreen clip (max 60s) of the game video.
    No cropping, just trimming.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return None

    output_path = video_path.replace(".mp4", "_widescreen.mp4")
    
    # If already exists, return (simple cache)
    if os.path.exists(output_path):
        return output_path
        
    logger.info(f"Generating widescreen clip for {game_id}...")
    
    try:
        clip = VideoFileClip(video_path)
        
        # Limit duration to 60s for Social Media (and performance)
        short_clip = clip.subclip(0, min(clip.duration, 60))
        
        # Write output
        short_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        clip.close()
        short_clip.close()
        
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate widescreen clip: {e}")
        return None
