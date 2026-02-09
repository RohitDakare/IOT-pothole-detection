# Smart Pothole Detection & Alert System - Architecture

## System Overview
The system is designed to detect potholes using LiDAR and Ultrasonic sensors, capture images via ESP32-CAM, tag the location with GPS, and upload data to a central dashboard via GSM.

## Hardware Architecture
1. **Raspberry Pi 4B**: Main brain, handles sensor fusion, coordinates ESP32-CAM, and manages data transmission.
2. **TF02 Pro LiDAR**: Measures high-precision distance to ground for pothole detection.
3. **HC-SR04 Ultrasonic**: Secondary validation of pothole depth.
4. **Neo-6M GPS**: Provides real-time coordinates.
5. **SIM800L GSM**: Transmits data to the web dashboard.
6. **ESP32-CAM**: Captures images triggered by Raspberry Pi.
7. **HC-05 Bluetooth**: Bluetooth manual control for the RC car.

## Logic Flow
1. **Manual Control**: RC car can be moved via Bluetooth commands ('f', 'b', 'l', 'r', 's').
2. **Detection**: LiDAR detects a sudden increase in distance (>5cm).
3. **Validation**: Ultrasonic sensor confirms the reading to avoid false positives.
4. **Capture**: Raspberry Pi triggers ESP32-CAM (GPIO 27 HIGH).
5. **Localization**: GPS fetches current Latitude/Longitude.
6. **Transmission**: 
    - Raspberry Pi sends sensor data via SIM800L GSM.
    - ESP32-CAM sends the image via WiFi (or GSM if bridged).
7. **Dashboard**: Stores data in MySQL, displays alerts on a Leaflet map.

## Pin Mapping (Raspberry Pi)
- **LiDAR (UART)**: TX -> GPIO 15, RX -> GPIO 14
- **Ultrasonic**: Trig -> GPIO 23, Echo -> GPIO 24
- **GPS (UART)**: TX -> GPIO 13, RX -> GPIO 12
- **GSM (UART)**: TX -> GPIO 1, RX -> GPIO 0
- **ESP32 Trigger**: GPIO 27
- **Bluetooth**: TX -> GPIO 14, RX -> GPIO 15 (SoftSerial or shared)
- **Motors (L298N)**: IN1:5, IN2:6, IN3:19, IN4:26, ENA:13, ENB:12
