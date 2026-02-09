import sys
import os
import time
import serial
import glob

# This script no longer needs RPi.GPIO or the custom SoftwareSerial.
# We will use 'pyserial' to scan hardware UARTs, which is more reliable.

def find_serial_ports():
    """Finds all potential serial ports on the system."""
    return sorted(glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyS*"))

def test_esp32_on_port(port, baud, timeout=5):
    """
    Tests for ESP32 communication on a single given hardware port.
    Sends a 'p' (ping) and waits for a 'PONG' response.
    """
    print(f"""
--- Checking Port: {port} @ {baud} baud ---""")
    ser = None
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=0.5)
        print(f"Port {port} opened. Sending 'ping' command ('p')...")

        # Clear any old data in buffer
        time.sleep(0.1)
        ser.read(ser.in_waiting)

        ser.write('p'.encode('utf-8'))
        
        start_time = time.time()
        response_buffer = ""
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                response_buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                if "PONG" in response_buffer:
                    print(f"✅ SUCCESS: Received 'PONG' from ESP32 on {port}.")
                    # Send capture command as final confirmation
                    ser.write('c'.encode('utf-8'))
                    print("Sent 'capture' command ('c'). Check for LED flash on ESP32-CAM.")
                    return "PASSED"
        
        print(f"TIMEOUT: No 'PONG' received on {port}.")
        if response_buffer:
            print(f"   - Full buffer received: '{response_buffer.strip()}'")
        return "FAILED"

    except serial.SerialException as e:
        print(f"ERROR: Could not open port {port}. It might be in use. {e}")
        return "FAILED"
    finally:
        if ser:
            ser.close()

def test_esp32():
    """
    Cycles through hardware UARTs to find and test an ESP32-CAM.
    This avoids using unstable Software Serial.
    """
    print("======================================================")
    print("=== Testing ESP32-CAM Comm (Hardware UART Scan)    ===")
    print("======================================================")
    print("This test scans hardware UARTs to find the ESP32-CAM.")
    print("It sends a 'p' (ping) and expects a 'PONG' response.")
    print("""
--- WIRING CONFIGURATION ---""")
    print("  - Connect ESP32-CAM U0TXD to a Pi RX pin (e.g., GPIO 13 / UART5_RX).")
    print("  - Connect ESP32-CAM U0RXD to a Pi TX pin (e.g., GPIO 12 / UART5_TX).")
    print("  - Ensure the corresponding UART is enabled in /boot/config.txt (e.g., dtoverlay=uart5).")
    
    # Baud rate must match the ESP32 firmware
    baud_rate = 115200
    print(f"  - Baud Rate: {baud_rate}")
    print("------------------------------------------------------")

    ports_to_check = find_serial_ports()
    if not ports_to_check:
        print("""
[CRITICAL] No hardware serial ports (/dev/ttyAMA*, /dev/ttyS*) found.""")
        final_status = "FAILED"
    else:
        print(f"""
[INFO] Will check ports: {ports_to_check}""")
        final_status = "FAILED"
        for port in ports_to_check:
            status = test_esp32_on_port(port, baud_rate)
            if status == "PASSED":
                final_status = "PASSED"
                break # Stop after first success

    print("""
==================== FINAL RESULT ====================""")
    if final_status == "PASSED":
        print("✅ ESP32-CAM communication test PASSED.")
    else:
        print("❌ ESP32-CAM communication test FAILED.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. ESP32 FIRMWARE: The ESP32 code MUST be programmed to listen for 'p' and respond with 'PONG' on its serial port.")
        print("   2. WIRING: Double-check that Pi's TX pin goes to ESP32's RX and vice-versa.")
        print("   3. BAUD RATE: Ensure baud rate in ESP32 code EXACTLY matches {baud_rate}.")
        print("   4. UART ENABLED: Is the correct hardware UART overlay enabled in /boot/config.txt?")
        print("   5. POWER: The ESP32-CAM requires a strong, stable 5V power supply.")
    print("======================================================")

if __name__ == "__main__":
    test_esp32()
