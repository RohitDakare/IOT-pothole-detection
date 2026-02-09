import serial
import time
import os
import glob
import sys

def find_serial_ports():
    """Finds all potential serial ports on the system."""
    # This covers hardware UARTs, USB-to-Serial converters, and virtual ports like rfcomm
    ports = glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyS*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/rfcomm*")
    return sorted(list(set(ports)))

def test_bluetooth(duration=10):
    """
    Scans available hardware serial ports for any incoming data,
    which is indicative of a working Bluetooth connection from a paired device.
    This test avoids using unstable software serial implementations.
    """
    print("======================================================")
    print("=== Testing HC-05 Bluetooth (Hardware UART Scan)   ===")
    print("======================================================")
    print("This test will scan all hardware serial ports for incoming data.")
    print("""
--- ACTION REQUIRED ---""")
    print("1. Ensure your phone is PAIRED with the 'HC-05' device.")
    print("2. Open a 'Serial Bluetooth Terminal' app on your phone.")
    print("3. CONNECT to the HC-05 module within the app.")
    print(f"4. You have {duration} seconds to CONTINUOUSLY SEND characters/text from the app.")
    print("""
--- WIRING CHECK ---""")
    print("  - This test assumes the HC-05 is connected to a HARDWARE UART.")
    print("  - Example (UART0): HC-05 TX -> Pi RX (GPIO 15), HC-05 RX -> Pi TX (GPIO 14).")
    print("  - Ensure the UART is enabled in /boot/config.txt (e.g., 'enable_uart=1').")
    print("------------------------------------------------------")

    ports = find_serial_ports()
    bauds = [9600, 38400, 115200] # Common baud rates for HC-05

    if not ports:
        print("""
[CRITICAL] No serial ports (/dev/ttyAMA*, /dev/ttyS*, etc.) found.""")
        print("==================== FINAL RESULT ====================")
        print("❌ Bluetooth test FAILED. No serial ports available to scan.")
        return

    print(f"""
[INFO] Will check ports: {ports}""")
    print(f"[INFO] Will check baud rates: {bauds}")
    print(f"[INFO] Listening for {duration} seconds... SEND DATA NOW.")

    found_data = False
    detection_details = {}
    
    start_time = time.time()
    # This loop runs for the total duration, repeatedly trying all port/baud combinations.
    # This allows the user time to connect and send data.
    while time.time() - start_time < duration and not found_data:
        for port_path in ports:
            if found_data: break
            if not os.path.exists(port_path): continue

            for baud in bauds:
                if found_data: break
                ser = None
                try:
                    # Use a very short timeout to scan quickly without blocking
                    ser = serial.Serial(port_path, baud, timeout=0.02)
                    
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        found_data = True
                        detection_details['port'] = port_path
                        detection_details['baud'] = baud
                        detection_details['data'] = data
                        break # Exit baud rate loop
                except serial.SerialException:
                    # Port may be in use or permissions error, just skip it
                    continue
                finally:
                    if ser:
                        ser.close()
        if not found_data:
            time.sleep(0.2) # Avoid busy-looping too fast; gives CPU a break

    print("""
==================== FINAL RESULT ====================""")
    if found_data:
        print("✅ Bluetooth test PASSED. Data was successfully received.")
        print(f"  - Detected on Port: {detection_details.get('port')}")
        print(f"  - At Baud Rate: {detection_details.get('baud')}")
        try:
            decoded_data = detection_details.get('data').decode('utf-8').strip()
            print(f"  - Sample Data Received: '{decoded_data}'")
        except UnicodeDecodeError:
            print(f"  - Sample Data (binary): {detection_details.get('data')}")
    else:
        print("❌ Bluetooth test FAILED. No data was received on any port in time.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. PHONE APP: Did you press 'CONNECT' in the app and are you actively sending data?")
        print("   2. WIRING: Is HC-05 TX wired to Pi RX on a hardware UART? (e.g., GPIO 14/15)")
        print("   3. UART ENABLED: Is the hardware UART enabled in '/boot/config.txt'?")
        print("   4. POWER: Ensure the HC-05 has a stable 5V supply and a common GND with the Pi.")
        print("   5. HC-05 LED: Should be blinking slowly (~2s interval) when connected via app.")
    print("======================================================")

if __name__ == "__main__":
    # This allows running the script with a custom duration, e.g., python3 test_bluetooth.py 20
    duration_arg = 10
    if len(sys.argv) > 1:
        try:
            duration_arg = int(sys.argv[1])
        except (ValueError, IndexError):
            print(f"Invalid duration provided. Using default {duration_arg} seconds.")
            
    test_bluetooth(duration=duration_arg)
