import serial
import time
import os
import glob

def check_uart_config():
    """Checks /boot/config.txt for UART-related settings."""
    print("--- [1] Checking UART Configuration (/boot/config.txt) ---")
    config_path = "/boot/config.txt"
    if not os.path.exists(config_path):
        # Fallback for newer Raspberry Pi OS versions
        config_path = "/boot/firmware/config.txt"

    if not os.path.exists(config_path):
        print("Warning: Could not find /boot/config.txt or /boot/firmware/config.txt.")
        return

    try:
        with open(config_path, "r") as f:
            content = f.read()
            print(f"  - 'enable_uart=1' found: {'enable_uart=1' in content}")
            print(f"  - 'dtoverlay=disable-bt' found: {'dtoverlay=disable-bt' in content} (Required for UART0 on GPIO 14/15)")
            for i in range(2, 6):
                if f'dtoverlay=uart{i}' in content:
                    print(f"  - 'dtoverlay=uart{i}' found: UART{i} is ENABLED")
    except Exception as e:
        print(f"Error: Could not read boot config file: {e}")

def find_serial_ports():
    """Finds and lists all potential serial devices in /dev/."""
    print("
--- [2] Checking For Active Serial Device Files ---")
    ports = glob.glob("/dev/ttyS*") + glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/rfcomm*")
    ports = sorted(list(set(ports)))
    if ports:
        print(f"Detected ports: {ports}")
    else:
        print("Warning: No serial ports (ttyS, ttyAMA, ttyUSB, rfcomm) detected in /dev/.")
    return ports

def scan_ports_for_data(ports):
    """Interactively scans specified ports and baud rates for incoming data."""
    print("
--- [3] Scanning All Ports for Incoming Data ---")
    print("
>>> ACTION: Start sending data continuously from your Bluetooth terminal app NOW! <<<")
    
    # Common baud rates for HC-05 modules
    bauds = [9600, 38400, 115200]
    
    print(f"Scanning ports {ports} at baud rates {bauds}.")
    print("Press Ctrl+C to stop the scan at any time.")

    try:
        while True:
            found_this_cycle = False
            for port_path in ports:
                if not os.path.exists(port_path):
                    continue
                
                for baud in bauds:
                    ser = None
                    try:
                        # Use a short timeout to avoid blocking
                        ser = serial.Serial(port_path, baud, timeout=0.05)
                        if ser.in_waiting > 0:
                            data = ser.read(ser.in_waiting)
                            print(f"

✨ DATA DETECTED! ✨")
                            print(f"  - PORT: {port_path}")
                            print(f"  - BAUD: {baud}")
                            print(f"  - RAW DATA: {data}")
                            try:
                                # Attempt to decode as text
                                print(f"  - DECODED: '{data.decode().strip()}'")
                            except UnicodeDecodeError:
                                print("  - DECODED: (Binary data, not valid UTF-8)")
                            print("-" * 20)
                            found_this_cycle = True
                    except (serial.SerialException, OSError):
                        # Port might be busy, in use, or permissions issue. Skip silently.
                        continue
                    finally:
                        if ser:
                            ser.close()
            
            if not found_this_cycle:
                print("Scanning... No data seen yet.", end="")

            time.sleep(0.2) # Small delay to reduce CPU usage
            
    except KeyboardInterrupt:
        print("

Scan stopped by user.")
    
    print("
--- 🔧 TROUBLESHOOTING CHECKLIST ---")
    print("1. WIRING: Is HC-05 'TX' connected to Pi 'RX' (and vice-versa) on a HARDWARE UART?")
    print("2. PINS: For UART0, use GPIO 14 (TX) & 15 (RX). Check 'WIRING_AND_PINOUT.md'.")
    print("3. POWER: The HC-05 needs a stable 5V supply and a shared GND with the Pi.")
    print("4. UART CONFIG: Is the correct UART enabled in '/boot/config.txt' (see step 1)?")
    print("5. BLUETOOTH PAIRING: Is your phone successfully paired with the 'HC-05' device?")
    print("6. PHONE APP: Did you press 'CONNECT' inside the Bluetooth terminal app?")

if __name__ == "__main__":
    check_uart_config()
    available_ports = find_serial_ports()
    if available_ports:
        scan_ports_for_data(available_ports)
    else:
        print("
Halting scan because no serial ports were found.")
