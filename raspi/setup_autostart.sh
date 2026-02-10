#!/bin/bash
# Script to install and enable the pothole detection service

SERVICE_NAME="pothole.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
SOURCE_PATH="/home/admin/main/IOT/raspi/pothole.service"

echo "Installing $SERVICE_NAME..."

# Check if source file exists
if [ ! -f "$SOURCE_PATH" ]; then
    echo "Error: Source service file not found at $SOURCE_PATH"
    exit 1
fi

# Copy service file to systemd directory (requires sudo)
sudo cp "$SOURCE_PATH" "$SERVICE_PATH"

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable "$SERVICE_NAME"

# Start the service immediately
sudo systemctl start "$SERVICE_NAME"

echo "✅ Service installed and started!"
echo "Check status with: sudo systemctl status $SERVICE_NAME"
