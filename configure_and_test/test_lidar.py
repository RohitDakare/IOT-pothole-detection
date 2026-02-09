import sys
import os
import time
import glob
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a mock for environments without RPi.GPIO
    class MockGPIO:
        BCM = 11
        def setmode(self, mode): pass
        def setwarnings(self, mode): pass
    GPIO = MockGPIO()
    print("Warning: RPi.GPIO not found. Using a mock library for syntax checking.")

# It's better to try to import the local module and handle the error gracefully
raspi_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'raspi'))
print(f"DEBUG: Appending {raspi_path} to sys.path")
sys.path.append(raspi_path)
print(f"DEBUG: sys.path after append: {sys.path}")

try:
    from sensors import LiDAR
    print("DEBUG: Successfully imported LiDAR from sensors.")
except ImportError as e:
    print(f"DEBUG: ImportError for sensors: {e}")
    print("Error: Could not import 'sensors' module from 'raspi' directory.")
    print("Ensure the file exists and this test is run from the 'configure_and_test' directory.")
    LiDAR = None

def find_serial_ports():
    """Finds all potential hardware serial ports on the system."""
    return sorted(glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyS*"))

def test_lidar_port(port, baud, duration=5):
    """Tests a specific serial port for LiDAR data."""
    if not LiDAR: return False

    print(f"""
--- Checking Port: {port} @ {baud} baud ---""")
    lidar_sensor = None
    try:
        # The LiDAR class from sensors.py is expected to handle serial initialization
        lidar_sensor = LiDAR(port=port, baud=baud)
        if not lidar_sensor.ser or not lidar_sensor.ser.is_open:
            print(f"Initialization failed on port {port}. It might be in use or invalid.")
            return False

        print(f"LiDAR Initialized on {port}. Reading for {duration} seconds...")
        
        start_time = time.time()
        valid_readings = 0
        
        while time.time() - start_time < duration:
            dist = lidar_sensor.get_distance()
            if dist is not None and dist > 0:
                valid_readings += 1
                # Print only the first success to avoid spamming the log
                if valid_readings == 1:
                    print(f"✅ SUCCESS: First valid distance on {port}: {dist:.2f} m")
            time.sleep(0.1)

        if valid_readings > 0:
            print(f"--- Test PASSED on {port} with {valid_readings} valid readings. ---")
            return True
        else:
            print(f"--- Test FAILED on {port}: No valid readings received. ---")
            return False
            
    except Exception as e:
        print(f"CRITICAL ERROR on {port}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # The LiDAR class should have a method to close the serial port
        if lidar_sensor and hasattr(lidar_sensor, 'close'):
            lidar_sensor.close()

def test_lidar():
    if LiDAR is None:
        print("Halting test because LiDAR class could not be imported.")
        return

    # Set GPIO mode just in case the sensor library relies on it, though it shouldn't for UART
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    print("====================================================")
    print("=== Testing LiDAR (TF02-Pro) - Hardware UART Scan ===")
    print("====================================================")
    print("This test prioritizes hardware UARTs for stability.")
    print("""
--- Recommended Wiring (UART4 - Confirmed Working) ---""")
    print("  - LiDAR Green (TX)  -> Pi Pin 21 (GPIO 9 / UART4_RX)")
    print("  - LiDAR Yellow (RX) -> Pi Pin 24 (GPIO 8 / UART4_TX)")
    print("  - LiDAR VCC (Red)   -> Pi Pin 2 or 4 (5V)")
    print("  - LiDAR GND (Black) -> Pi GND (Any GND pin)")
    print("  - Ensure 'dtoverlay=uart4' is in /boot/config.txt")
    print("----------------------------------------------------")

    # Baud rate for TF02-Pro is typically 115200
    baud_rate = 115200
    
    # Prioritize /dev/ttyAMA4 since tests confirmed LiDAR is connected there
    all_ports = find_serial_ports()
    # Move /dev/ttyAMA4 to the front if it exists
    ports_to_check = []
    if '/dev/ttyAMA4' in all_ports:
        ports_to_check.append('/dev/ttyAMA4')
    ports_to_check.extend([p for p in all_ports if p != '/dev/ttyAMA4'])

    if not ports_to_check:
        print("""
[CRITICAL] No hardware serial ports found to scan.""")
        found_lidar = False
    else:
        print(f"""
[INFO] Will check ports: {ports_to_check} at {baud_rate} baud.""")
        found_lidar = False
        for port in ports_to_check:
            if test_lidar_port(port, baud_rate):
                found_lidar = True
                break # Stop after first successful detection

    print("""
==================== FINAL RESULT ====================""")
    if found_lidar:
        print("✅ LiDAR test PASSED. A valid connection was established.")
    else:
        print("❌ LiDAR test FAILED. Not detected on any standard hardware UART port.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. WIRING: Verify LiDAR TX->Pi RX and LiDAR RX->Pi TX connections.")
        print("      - LiDAR Green (TX) -> GPIO 9 (Pin 21)")
        print("      - LiDAR Yellow (RX) -> GPIO 8 (Pin 24)")
        print("   2. UART ENABLED: Ensure 'dtoverlay=uart4' is in '/boot/config.txt'.")
        print("   3. POWER: LiDAR requires a stable 5V supply and a common GND with the Pi.")
        print("   4. BAUD RATE: Confirm the sensor is configured for 115200 baud.")
        print("   5. PERMISSIONS: Try 'sudo chmod 666 /dev/ttyAMA4' if permission denied.")
    print("====================================================")

if __name__ == "__main__":
    test_lidar()
