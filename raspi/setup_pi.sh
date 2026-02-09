#!/bin/bash

# Update and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-serial python3-rpi.gpio

# Install python libraries
pip3 install -r requirements.txt --break-system-packages

echo "Setup complete. You can now run the system using: python3 main.py"
