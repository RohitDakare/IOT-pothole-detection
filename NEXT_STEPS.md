# Step-by-Step Action Plan: Smart Pothole Detection System (UPDATED)

Backend and Dashboard are now fully integrated. Follow these steps to get the whole system live.

---

## ✅ Phase 1: Local Backend & Dashboard (Ready to Go)
*Goal: Get your server running on your PC.*

1. **NO SETUP REQUIRED**: 
   - I have switched the system to **SQLite**. 
   - You **do not** need MySQL anymore. 
   - No passwords or database creation needed!

2. **Run the Backend**:
   - Double-click the file: `backend/run_backend.bat`.
   - The system will automatically create the database file (`pothole_system.db`) for you.
   - Keep this window open!

3. **Verify Dashboard**:
   - Open your browser and go to `http://localhost:8000`.
   - You should see the dark-mode map.

4. **Optional: Test the Map**:
   - Run `python test_api_mock.py` in a new terminal. 
   - Watch the dashboard; pins should start appearing automatically!

---

## 🕒 Phase 2: Raspberry Pi Configuration (Next Task)
*Goal: Get the RC car's brain working.*

1. **Complete SSH Transfer**:
   - Ensure the `raspi/` folder has finished copying to your Pi.

2. **Run the Pi Installer**:
   - In your Pi terminal, run:
     ```bash
     cd ~/pothole_detection
     chmod +x setup_pi.sh
     ./setup_pi.sh
     ```

3. **Update Server URL (If necessary)**:
   - If your PC's IP address has changed, update the `URL` in `raspi/communication.py` (Line 25) to match your PC's local IP.

4. **Start Detection**:
   - Run: `python3 main.py`.

---

## 🛠️ Phase 3: Hardware & ESP32-CAM
*Goal: Final hardware assembly.*

1. **Flash the Camera**:
   - Open `esp32cam/esp32cam.ino` in Arduino IDE.
   - Update your **WiFi SSID and Password**.
   - Ensure `serverUrl` (Line 30) points to your PC's IP address.
   - Upload to the ESP32-CAM.

2. **Wiring Verification**:
   - Follow the layout in `docs/Architecture.md`.
   - **Critical**: Ensure the Raspberry Pi GND is connected to the L298N Motor Driver GND and the ESP32-CAM GND.

---

## 🚗 Phase 4: Live Demonstration
1. **Connect Bluetooth**: Pair with HC-05.
2. **Drive**: Use terminal commands (`f`, `b`, `l`, `r`).
3. **Detection**: Drive over a gap of 5cm+. 
4. **Alert**: Watch the LED on the ESP32-CAM flash and the dashboard update instantly!
