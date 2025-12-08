#!/bin/bash

# Soccer Cam Installer for Raspberry Pi 5

set -e

echo "Installing System Dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv git libcamera-apps vlc-bin- checkinstall build-essential chrony

# Setup Directory
INSTALL_DIR="/home/pi/soccer_rig"
RECORDINGS_DIR="/home/pi/Recordings"

echo "Setting up Directories..."
mkdir -p "$RECORDINGS_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/cmc0619/Traloxolcus-Gemini.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Python Venv
echo "Setting up Python Environment..."
if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Systemd
echo "Configuring Systemd Service..."
sudo cp soccer-cam.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable soccer-cam.service
sudo systemctl start soccer-cam.service

echo "Installation Complete!"
echo "Access the UI at http://$(hostname -I | awk '{print $1}'):8000"
