# �️ Smart Pothole Detection & Mapping System

A comprehensive IoT-based solution for real-time pothole detection using Ultrasonic sensors, GPS, and Machine Learning. The system includes a central dashboard, a Python backend, and hardware logic for Raspberry Pi and ESP32-CAM.

---

## 🏗️ System Architecture Overview
1.  **Backend (PC/Server):** FastAPI handles data storage (SQLite) and serves the Dashboard.
2.  **Dashboard (Web):** Real-time Google Maps integration showing pothole locations and severity.
3.  **Raspberry Pi (Robot):** Main controller for motors, GPS location, and data transmission over GSM.
4.  **ESP32-CAM (Vision):** Captures visual proof of potholes upon detection.

---

## 💻 1. Backend & Dashboard Setup (Server-side)

The backend is built with FastAPI and uses a local SQLite database (`pothole_system.db`).

### **Prerequisites**
- Python 3.10 or higher installed on your system.

### **Installation Steps**
1.  **Navigate to the backend directory:**
    ```powershell
    cd backend
    ```
2.  **Install dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
3.  **Launch the Server:**
    - Method A: Double-click `run_backend.bat`.
    - Method B: Run manually via terminal:
      ```powershell
      python main.py
      ```
4.  **Access the Dashboard:**
    - Open your browser and go to: `http://localhost:8000`

---

## 🧪 2. Mock Testing (Simulation)

To test the dashboard functionality without hardware, you can simulate pothole detections.

1.  **Keep the Backend running.**
2.  **Run the mock script:**
    ```powershell
    python test_api_mock.py
    ```
3.  New markers will appear on the dashboard map every 10 seconds near Mumbai (demo coordinates).

---

## 🤖 3. Raspberry Pi Configuration (On Robot)

The Pi acts as the brain of the robot, managing the **Ultrasonic sensor**, **NEO-6M GPS**, **SIM800L GSM**, and **Motors**.

### **Setup on Pi**
1.  **Transfer the `raspi/` folder** to your Raspberry Pi via SCP or USB.
2.  **Install system dependencies:**
    ```bash
    sudo apt-get update
    sudo apt-get install python3-pip
    ```
3.  **Run the setup script (Optional but recommended):**
    ```bash
    cd raspi
    chmod +x setup_pi.sh
    ./setup_pi.sh
    ```
4.  **Configure API URL:**
    - Edit `raspi/communication.py` and ensure the `BACKEND_URL` matches your PC's IP address (e.g., `http://192.168.1.10:8000`).

5.  **Run the Logics:**
    ```bash
    python3 main.py
    ```

---

## 📷 4. ESP32-CAM Setup (Vision)

The ESP32-CAM captures images once triggered by the Raspberry Pi over a Serial/GPIO signal.

1.  **Open Arduino IDE.**
2.  **Open File:** `esp32cam/esp32cam.ino`.
3.  **Configuration:** Update the following in the code:
    - `WIFI_SSID`: Your WiFi Name.
    - `WIFI_PASSWORD`: Your WiFi Password.
    - `serverUrl`: Your PC's Local IP (e.g., `http://192.168.1.10:8000/api/upload_image`).
4.  **Flash:**
    - Select Board: `AI Thinker ESP32-CAM`.
    - Connect via FTDI adapter and upload.

---

## 🎮 5. Operation & Controls

### **Motion Control (Bluetooth)**
Pair your PC or Phone with the **HC-05 Bluetooth module** and use any Serial Terminal app:
- `f`: Move Forward
- `b`: Move Backward
- `l`: Turn Left
- `r`: Turn Right
- `s`: Stop

### **Detection Parameters**
- **Trigger**: When depth > 5cm is detected by the Ultrasonic sensor.
- **Data Flow**: Detection -> GSM -> Backend -> Google Maps Dashboard.
- **Visuals**: ESP32-CAM flashes and uploads the photo automatically.

---

## 🛠️ Troubleshooting
- **Dashboard Empty?** Ensure the backend is running and `pothole_system.db` is initialized. Refresh the page.
- **Hardware not connecting?** Check if the Raspberry Pi and ESP32 are on the same WiFi network as your PC.
- **GPS No Fix?** GPS modules require a clear view of the sky (Outdoor testing recommended).
- **GSM Error?** Ensure the SIM card has an active data plan and the module is getting at least 2A of current.

---
*Created for the Smart Pothole Detection Internship Project.*
