#!/bin/bash

# =================================================================
# Smart Pothole Detection & Mapping System - All-in-One Runner
# This script starts the Backend and the Detection Engine.
# =================================================================

# Color codes for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Initializing Smart Pothole Detection System...${NC}"

# 1. Start the Backend API (FastAPI)
echo -e "${GREEN}[1/2] Starting Backend Server...${NC}"
python3 backend/main.py > logs/backend_output.log 2>&1 &
BACKEND_PID=$!
echo "Backend running with PID: $BACKEND_PID"

# Wait a few seconds for the server to initialize
sleep 3

# 2. Start the Pothole Detection Logic
echo -e "${GREEN}[2/2] Starting Detection Engine (LiDAR + GPS + ML)...${NC}"
python3 raspi/main2.py > logs/pothole_detection.log 2>&1 &
DETECTION_PID=$!
echo "Detection Engine running with PID: $DETECTION_PID"

echo -e "${BLUE}=====================================================${NC}"
echo -e "SYSTEM ONLINE!"
echo -e "Dashboard: http://localhost:8000"
echo -e "3D Map:    http://localhost:8000/3d-map"
echo -e "Logs:      Check the 'logs/' directory"
echo -e "To Stop:   run 'kill $BACKEND_PID $DETECTION_PID'"
echo -e "${BLUE}=====================================================${NC}"

# Keep the script alive and follow the detection log
tail -f logs/pothole_detection.log
