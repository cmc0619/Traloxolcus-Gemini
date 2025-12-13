# Traloxolcus-Gemini: Autonomous Soccer Recording System

[![Component: Rig](https://img.shields.io/badge/Component-Rig-blue)](./soccer_rig)
[![Component: Bench](https://img.shields.io/badge/Component-Bench-green)](./soccer_bench)
[![Component: Platform](https://img.shields.io/badge/Component-Platform-purple)](./soccer_platform)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Traloxolcus-Gemini** is a professional-grade, open-source system for recording, processing, and analyzing youth soccer matches using a synchronized multi-camera setup.

## 🏗️ Architecture

The system is composed of three distinct tiers:

| Tier | Component | Hardware | Function |
|:---|:---|:---|:---|
| **Tier 1 (Edge)** | **[Rig](./soccer_rig)** | Raspberry Pi 5 + IMX686 | 3x Synchronized Field Cameras (Left, Center, Right) capturing 4K video. WiFi Mesh communication. |
| **Tier 2 (Local)** | **[Bench](./soccer_bench)** | Laptop/Workstation (GPU) | Ingests footage from Rigs, stitches panoramic video, runs ML analysis, and uploads to Platform. |
| **Tier 3 (Cloud)** | **[Platform](./soccer_platform)** | VPS/Cloud Server | Central API, Database, and Web Interface for managing teams, players, and match archives. |

---

## 🚀 Quick Start

### 1. The Platform (Cloud/API)

The backend service that stores user data, team info, and match metadata.

```bash
# Start the full stack (Platform + DB + Nginx)
docker compose up -d --build
```

Access the Platform API docs at `http://localhost:8000/docs` (or via configured Nginx port).

### 2. The Bench (Processing Station)

Runs on your powerful local machine to offload footage from cameras.

```bash
# Start the Bench Ingest & Processing services
docker compose -f docker-compose.bench.yml up -d --build
```

Access the Bench Dashboard at `http://localhost:4421`.

### 3. The Rig (Camera Node)

Runs on Raspberry Pi 5 hardware.

**Installation on Pi:**

```bash
./install.sh
```

**Manual Dev Run:**

```bash
cd soccer_rig
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access the Camera UI at `http://<PI_IP>:8000`.

---

## 🛠️ Features

* **Synchronized Recording**: Center camera acts as NTP master for <5ms drift.
* **Auto-Ingest**: 'Bench' auto-discovers cameras on the local mesh and pulls footage.
* **ML Pipeline**: Automatic stitching of 3 camera feeds into a tactical panoramic view.
* **Security**: Role-based access control (Admin/Coach/Player).
* **Self-Healing**: Automated health checks, disk management, and battery monitoring on Rigs.
* **Updates**: Over-the-air updates for Camera Nodes via GitHub Releases.

## 📚 Documentation

* **[Specification](./SPEC.md)**: Detailed technical specifications.
* **[Architecture Proposal](./ARCHITECTURE_PROPOSAL.md)**: In-depth design decisions.
* **[Tasks](./TASKS.md)**: Current roadmap and todo list.

## 🤝 Contribution

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
