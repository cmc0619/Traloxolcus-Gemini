# Walkthrough - Soccer Analytics System

## Audit & Fixes (2025-12-09)

We performed a system-wide audit and implemented the following critical fixes:

1. **Admin Creation (`create_admin.py`)**: Added `soccer_platform/create_admin.py` to bootstrap the first superuser.
2. **Schema Alignment**: Updated `soccer_bench/analysis.py` to output JSONL matching the Platform's `EventCreate` schema (added `type`, `metadata`).
3. **Robust Ingest**: Updated `soccer_bench/stitcher.py` with Regex to safely parse filenames containing underscores (e.g., `match_day_1_CAM_L...`).
4. **Deployment Split**: Verified and documented the split deployment (Home vs Cloud).

---

## Deployment Guide

### Option A: Local Full Stack (Dev)

Run everything on one machine:

```bash
docker-compose up --build
```

Access Platform at `http://localhost:8000`.

### Option B: Production Split (Hybrid)

**1. The Platform (Cloud VPS)**
Runs the Database and Web Interface.

```bash
# Upload code to VPS, then:
docker-compose -f docker-compose.platform.yml up -d --build
# Create Admin
docker exec -it soccer_platform python soccer_platform/create_admin.py --username admin --password secret
```

**2. The Bench (Home GPU)**
Runs Ingest, Stitching, and ML.

```bash
# Set URL to your VPS
export PLATFORM_URL=http://<VPS_IP_ADDRESS>:8000
# Run Bench
docker-compose -f docker-compose.bench.yml up -d --build
```

The Bench will auto-discover Rigs on the LAN, process footage, and upload results to the Platform URL.
