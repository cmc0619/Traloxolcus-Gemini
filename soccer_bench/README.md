# Soccer Bench (Processing Station)

This component runs on a powerful Local Machine (e.g., Desktop with NVIDIA GPU).

## Responsibilities

1. **Ingest**: Connects to Raspberry Pis via WiFi/LAN and pulls raw 4K footage.
2. **Process**:
    * **Stitching**: Merges CAM_L, CAM_C, CAM_R into a single panoramic view.
    * **ML Analysis**: Runs object detection and event recognition.
3. **Upload**: Sends the final processed video and metadata to the Cloud Platform.

## Requirements

* Python 3.10+
* FFmpeg (with NVENC support)
* NVIDIA Drivers (CUDA)
