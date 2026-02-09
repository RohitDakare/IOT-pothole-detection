import serial
import time
import os

def check_for_nmea(line):
    """Checks if a line is a valid NMEA sentence (starts with '$' and has a checksum)."""
    return line.startswith('$') and len(line) > 6 and '*' in line

def has_fix(line):
    """
    Checks a $GPGGA sentence for a quality fix.
    A fix quality of '1' (GPS) or '2' (DGPS) is considered valid.
    """
    if line.startswith('$GPGGA'):
        parts = line.split(',')
        # Field 6 is the Fix Quality Indicator (0=Invalid, 1=GPS, 2=DGPS)
        if len(parts) > 6 and parts[6] in ('1', '2'):
            return True
    return False

def test_gps_port(port, baud, duration=10):
    """Tests a single serial port for valid GPS NMEA data and a satellite fix."""
    print(f"""
--- Checking Port: {port} @ {baud} baud ---""")
    ser = None
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1)
        print(f"Port opened. Listening for {duration} seconds for NMEA data...")

        start_time = time.time()
        found_data = False
        found_fix = False
        
        while time.time() - start_time < duration:
            # Using readline() is efficient for NMEA sentences
            line = ser.readline().decode('ascii', errors='ignore').strip()
            
            if line and check_for_nmea(line):
                if not found_data:
                    print(f"✅ SUCCESS: NMEA data detected on {port}!")
                    print(f"   Sample: {line}")
                    found_data = True

                if has_fix(line):
                    print(f"✅ SUCCESS: GPS SATELLITE FIX ACQUIRED on {port}!")
                    print(f"   Data: {line}")
                    found_fix = True
                    break # Exit loop once fix is confirmed
        
        if found_fix:
            print(f"--- Test PASSED on {port} ---")
            return "FIX"
        if found_data:
            print(f"--- Test PARTIALLY PASSED on {port}: Data found, but no satellite fix yet. ---")
            return "DATA"
            
        print(f"--- Test FAILED on {port}: No NMEA data detected. ---")
        return "NONE"

    except serial.SerialException as e:
        print(f"ERROR: Could not open port {port}. It may be in use or lack permissions. {e}")
        return "NONE"
    except Exception as e:
        print(f"An unexpected error occurred on port {port}: {e}")
        return "NONE"
    finally:
        if ser:
            ser.close()

def test_gps():
    """
    Scans all likely hardware UART ports for a GPS module.
    """
    print("====================================================")
    print("=== Testing NEO-6M GPS (Hardware UART Scan)      ===")
    print("====================================================")
    print("This script checks hardware UARTs for NMEA data and a satellite fix.")
    print("""
--- Recommended Wiring (Hardware UART) ---""")
    print("  - GPS TX -> Pi RX (e.g., GPIO 15 / UART0_RX)")
    print("  - GPS RX -> Pi TX (e.g., GPIO 14 / UART0_TX)")
    print("  - Ensure 'enable_uart=1' is in /boot/config.txt and console is disabled on the port.")
    print("----------------------------------------------------")

    # Hardware UARTs on Pi, in order of common use for GPS
    ports_to_check = ["/dev/ttyAMA0", "/dev/ttyS0", "/dev/ttyAMA1", "/dev/ttyAMA2", "/dev/ttyAMA3", "/dev/ttyAMA4", "/dev/ttyAMA5"]
    baud_rate = 9600 # Standard for most GPS modules like NEO-6M
    
    final_status = "NONE"

    for port in ports_to_check:
        if os.path.exists(port):
            status = test_gps_port(port, baud_rate)
            if status == "FIX":
                final_status = "FIX"
                break # Success! No need to check other ports.
            if status == "DATA" and final_status != "FIX":
                final_status = "DATA" # Found data, but keep searching for a port with a better fix.
        else:
            print(f"""
--- Port {port} not found. Skipping. ---""")

    print("""
==================== FINAL RESULT ====================""")
    if final_status == "FIX":
        print("✅ GPS test PASSED. A satellite fix was successfully acquired.")
    elif final_status == "DATA":
        print("⚠️ GPS test PARTIALLY PASSED. Data is being received, but no satellite fix.")
        print("   This is common and may resolve on its own.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. LOCATION: Move the GPS antenna to a location with a clear, open view of the sky.")
        print("   2. TIME: A cold start can take several minutes to get the first fix. Wait longer.")
        print("   3. ANTENNA: Check the GPS antenna connection. Is it securely attached?")
    else: # final_status == "NONE"
        print("❌ GPS test FAILED. No NMEA data was detected on any port.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. WIRING: Check that GPS TX is connected to Pi RX and GPS RX to Pi TX.")
        print("   2. POWER: Ensure the NEO-6M has a stable 3.3V or 5V supply and solid GND.")
        print("   3. UART ENABLED: Make sure the correct UART is enabled in /boot/config.txt (e.g., 'enable_uart=1').")
        print("   4. SERIAL CONSOLE: Ensure the serial port is not being used by the Linux console.")
        print("      Run 'sudo raspi-config' -> Interface Options -> Serial Port -> NO to login shell, YES to hardware port.")
    print("====================================================")

if __name__ == "__main__":
    test_gps()
