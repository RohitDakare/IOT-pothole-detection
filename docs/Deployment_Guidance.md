# Deployment & Setup Guidance

## 1. Raspberry Pi Setup
- **Enable Interfaces**: Run `sudo raspi-config` and enable I2C, Serial Port (Disable login shell, Keep hardware serial), and Camera if using CSI (though we use ESP32-CAM via GPIO trigger).
- **Install Dependencies**:
  ```bash
  pip install pyserial adafruit-circuitpython-gps RPi.GPIO requests
  ```
- **Virtual Network**: 
  - Install Mosquitto if using MQTT for real-time dashboard updates: `sudo apt install mosquitto mosquitto-clients`.

## 2. Power & Hardware
- **Buck Converter**: Ensure the LM2596 is precisely tuned to 5.1V. Measure with a multimeter before connecting to the Pi.
- **Common Ground**: Ensure all modules (GPS, GSM, LiDAR, ESP32-CAM, Pi) share a single ground rail on the breadboard.
- **SIM800L Power**: This module peaks at 2A. If the Pi reboots when GSM transmits, use a separate 5V supply for the GSM with a common ground.

## 3. ESP32-CAM Setup
- Use an FTDI Programmer (USB-to-TTL) to upload the code from `esp32cam/esp32cam.ino`.
- Match the `triggerPin` (GPIO 12) with the Raspberry Pi GPIO 27.

## 4. Dashboard Deployment
- Deploy the backend (FastAPI/Node.js) to a server with a public IP (e.g., the mentioned `195.35.23.26`).
- Use Docker to containerize the dashboard and database for easy deployment.
  ```yaml
  # Sample Docker Compose
  services:
    db:
      image: mysql:latest
    backend:
      build: ./backend
    frontend:
      image: nextjs-dashboard
  ```

## 5. RC Car Integration
- Connect the HC-05 Bluetooth module to the Pi's UART (GPIO 9, 10).
- Use a simple Python script to listen for Bluetooth commands and drive the RC car motors via an L298N motor driver or similar.
