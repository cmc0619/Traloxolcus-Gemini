FROM python:3.10-slim

# Install System Deps (FFmpeg for Stitcher, GL for OpenCV)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Requirements
COPY soccer_bench/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1

# Run
CMD ["python", "-m", "soccer_bench.main"]
