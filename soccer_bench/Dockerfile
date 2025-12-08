FROM ultralytics/ultralytics:latest

# Install FFmpeg (with some hardware libs if available in repos, 
# though compiling for NVENC strictly might be needed for full speed. 
# For now, we use standard ffmpeg and hope the base image/drivers map through).
# Note: The base ultralytics image assumes NVIDIA runtime mapping.

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1

# Command
# Runs the daemon by default
CMD ["python", "-m", "soccer_bench.daemon"]
