#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

echo "Activating Python virtual environment..."
source venv/bin/activate

echo "Starting Pothole Detection System in background and logging to pothole_system.log..."
python3 raspi/main.py > pothole_system.log 2>&1 &
echo $! > pothole_system.pid

echo "Displaying real-time logs (Ctrl+C to stop viewing logs, system will continue running in background)."
tail -f pothole_system.log

echo "Pothole Detection System logging stopped. The system is still running in the background."
