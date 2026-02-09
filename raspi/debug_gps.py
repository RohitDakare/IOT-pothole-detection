import serial
import time
import sys

# Comprehensive GPS Diagnostic
# 1. Scans all standard UART ports
# 2. Scans multiple baud rates
# 3. Output raw NMEA data for verification

def test_port(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=2)
        print(f"Checking {port} at {baud} baud...", end="", flush=True)
        time.sleep(1.5) # Wait for data
        print(".", end="", flush=True)
        
        if ser.in_waiting > 0:
            # Read a chunk
            raw = ser.read(ser.in_waiting)
            try:
                decoded = raw.decode('ascii', errors='replace')
                # Check for standard NMEA headers
                if "$GP" in decoded or "$GN" in decoded:
                    print(f"\n[SUCCESS] NMEA data detected on {port} @ {baud}!")
                    print(f"Sample: {decoded[:100].strip()}...")
                    ser.close()
                    return True
                else:
                    print(f"\n[WARNING] Data received but not NMEA (Noise/Wrong Baud).")
                    print(f"Sample: {raw[:20]}")
            except:
                print(f"\n[WARNING] Binary/Garbage data received.")
        else:
            print(" No Data.")
        
        ser.close()
    except OSError:
        print(" Port busy or unavailable.")
    except Exception as e:
        print(f" Error: {e}")
    return False

def main():
    print("=== ULTRA GPS DIAGNOSTIC TOOL ===")
    print("Expected: UART5 (GPIO 12/13) -> /dev/ttyAMA5")
    
    ports = [
        "/dev/ttyAMA5", # wiring requirement
        "/dev/ttyAMA4",
        "/dev/ttyAMA1", 
        "/dev/ttyS0", 
        "/dev/serial0",
        "/dev/ttyUSB0"
    ]
    
    bauds = [9600, 115200, 38400, 4800]
    
    found = False
    
    for port in ports:
        for baud in bauds:
            if test_port(port, baud):
                found = True
                print(f"\n>> RECOMMENDATION: Configure sensors.py to use PORT={port}, BAUD={baud}")
                break
        if found: break
    
    if not found:
        print("\n[FAILURE] No GPS found.")
        print("Check:")
        print("1. Wiring: TX(GPS) -> RX(Pi GPIO 12), RX(GPS) -> TX(Pi GPIO 13)")
        print("2. Power: GPS Red LED should be blinking ( Fix) or Solid (Power)")
        print("3. UARTS: Did you run './enable_uarts.sh' and REBOOT?")

if __name__ == "__main__":
    main()
