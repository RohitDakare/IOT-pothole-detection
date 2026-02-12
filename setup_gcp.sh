#!/bin/bash

# Auto-Setup Script for Google Cloud Platform (GCP) Deployment
# Run this script on your VM instance after uploading your project folder.

# 1. Update System
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install Python & Utilities
echo "Installing Python3, pip, and venv..."
sudo apt install python3-pip python3-venv unzip -y

# 3. Create Virtual Environment
echo "Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 4. Install Requirements
echo "Installing dependencies..."
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
else
    echo "Error: backend/requirements.txt not found!"
    exit 1
fi

# 5. Create Systemd Service for Persistence
PROJECT_DIR=$(pwd)
USER_NAME=$(whoami)

echo "Creating systemd service 'pothole-backend'..."
SERVICE_FILE="/etc/systemd/system/pothole-backend.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Pothole Detection Backend Service
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python3 backend/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Enable & Start Service
echo "Enabling and Starting Service..."
sudo systemctl daemon-reload
sudo systemctl enable pothole-backend
sudo systemctl restart pothole-backend

# 7. Check Status
echo "Service Status:"
sudo systemctl status pothole-backend --no-pager

# 8. Firewall Reminder
echo "========================================================"
echo "DEPLOYMENT COMPLETE!"
echo ""
echo "Please ENSURE you have opened port 8000 in GCP Firewall."
echo "Go to: VPC Network > Firewall > Create Firewall Rule"
echo "  - Targets: All instances in the network"
echo "  - Source IP ranges: 0.0.0.0/0"
echo "  - Protocols and ports: tcp:8000"
echo "========================================================"
