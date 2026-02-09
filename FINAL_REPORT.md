# Smart Pothole Detection & Alert System - Implementation Report

## 1. System Architecture
The system follows a distributed architecture:
- **Edge Layer (RC Car)**:
    - **Raspberry Pi 4B**: Coordinates motor control (Bluetooth), sensor fusion (LiDAR + Ultrasonic), and localization (GPS).
    - **ESP32-CAM**: Captured multi-perspective images of potholes triggered by the Pi.
- **Network Layer**:
    - **GSM (SIM800L)**: Primary data link for telemetry.
    - **WiFi**: Secondary link for high-bandwidth image transmission from ESP32-CAM.
- **Cloud Layer**:
    - **FastAPI Backend**: Processes incoming JSON telemetry and binary images.
    - **MySQL Database**: Persistent storage for pothole historical data and repair tracking.
- **Control Layer**:
    - **Web Dashboard**: Leaflet.js based real-time map visualization with severity analytics.

## 2. YOLO Integration Steps
Since real-time YOLOv8 can be heavy for a Raspberry Pi 4, we recommend using **YOLOv8-Nano (TFLite)**:

### Prerequisites
```bash
pip install ultralytics opencv-python tensorflow
```

### Integration Logic
1. **Model Export**: Export a pothole-trained YOLOv8 model to TFLite format.
2. **Inference Loop**:
   - Capture frames using OpenCV from a USB camera or ESP32-CAM stream.
   - Run inference.
   - If a 'pothole' class is detected with confidence > 0.6, trigger the sensor validation.
3. **Sensor Fusion**: Only report a pothole if *both* YOLO detects it *and* the LiDAR measures a distance drop.

### Sample Code Snippet
```python
from ultralytics import YOLO
import cv2

model = YOLO('pothole_n.tflite', task='detect') # Use TFLite for speed

def cv_detection():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        results = model(frame, stream=True)
        for r in results:
            if 'pothole' in r.names and r.probs.max() > 0.6:
                # Signal the PotholeSystem to validate with LiDAR
                pass
```

## 3. Deployment Guidance
### Raspberry Pi
1. Run `./setup_pi.sh` to install system dependencies.
2. Ensure UART is enabled in `raspi-config`.
3. Run `python3 main.py`.

### ESP32-CAM
1. Open `esp32cam.ino` in Arduino IDE.
2. Install `ESP32` board manager and select `AI Thinker ESP32-CAM`.
3. Update WiFi credentials and flash.

### Backend/Cloud
1. Import `schema.sql` into your MySQL instance.
2. Run `uvicorn main:app --host 0.0.0.0 --port 80`.
3. Serve `dashboard/index.html` via Nginx or a simple HTTP server.

## 4. Key Logic (Verification Pass)
To track repair status (Red -> Green):
- When the RC car passes over a known pothole coordinate again:
- The system checks the `depth` via LiDAR.
- If `current_depth < threshold`, the system sends a `status='Green'` update to the API.
- The API calculates the `repair_time_hours` automatically based on the SQL schema.
---
**Note:** All source files can be found in the `raspi/`, `esp32cam/`, `backend/`, and `dashboard/` directories.
