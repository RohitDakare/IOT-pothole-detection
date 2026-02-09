import sys
import os
import time
import serial
import glob

def find_serial_ports():
    """Finds all potential hardware serial ports on the system."""
    return sorted(glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyS*"))

def send_at_command(ser, command, timeout=2):
    """
    Sends an AT command to the modem, reads the response, and cleans it up.
    Returns a list of response lines.
    """
    if not ser or not ser.is_open:
        print("[ERROR] Serial port is not open.")
        return []

    print(f"""
[COMMAND] > {command}""")
    
    # Clear any old data in the buffer to ensure a clean read
    ser.reset_input_buffer()
        
    ser.write((command + '\r\n').encode('utf-8'))
    
    response_lines = []
    start_time = time.time()
    
    # Read lines until timeout
    while time.time() - start_time < timeout:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            response_lines.append(line)
        # A short sleep to prevent busy-waiting, but allow for fast responses
        time.sleep(0.05)

    print(f"[RESPONSE] > {response_lines}")
    return response_lines

def test_gsm_on_port(port, baud):
    """
    Runs a full diagnostic suite on a given port.
    """
    print(f"""
--- Checking Port: {port} @ {baud} baud ---""")
    ser = None
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print(f"Port {port} opened. Starting diagnostics...")

        results = {}
        # Test 1: Basic Communication
        response = send_at_command(ser, "AT")
        results['communication'] = 'OK' in response

        # Test 2: SIM Card Status
        response = send_at_command(ser, "AT+CPIN?")
        results['sim_status'] = any('+CPIN: READY' in s for s in response)

        # Test 3: Network Registration
        response = send_at_command(ser, "AT+CREG?")
        # CREG: x,1 means registered, home network. x,5 is registered, roaming.
        results['network_reg'] = any(status in ''.join(response) for status in ["+CREG: 0,1", "+CREG: 1,1", "+CREG: 0,5", "+CREG: 1,5"])

        # Test 4: Signal Strength
        response = send_at_command(ser, "AT+CSQ")
        results['signal_strength'] = False
        for line in response:
            if line.startswith('+CSQ:'):
                try:
                    # e.g., from '+CSQ: 18,0' -> 18
                    strength = int(line.split(':')[1].split(',')[0].strip())
                    # 0 is low signal, 99 is not known. We want something in between.
                    if 0 < strength < 99:
                        results['signal_strength'] = True
                except (ValueError, IndexError):
                    results['signal_strength'] = False
        
        return results

    except serial.SerialException as e:
        print(f"ERROR: Could not open port {port}. It may be in use. {e}")
        return None
    finally:
        if ser:
            ser.close()

def test_gsm():
    print("====================================================")
    print("=== Testing SIM800L GSM (Hardware UART Scan)     ===")
    print("====================================================")
    print("This test scans hardware UARTs to find and test the SIM800L module.")
    print("""
--- PREREQUISITES ---""")
    print("1. A valid, activated SIM card (with PIN disabled) MUST be inserted.")
    print("2. The SIM800L requires a SEPARATE, high-current power supply (e.g., 3.7V LiPo).")
    print("   DO NOT power it directly from the Pi's 3.3V or 5V pins.")
    print("3. Connect SIM800L TX to Pi RX and SIM800L RX to Pi TX on a hardware UART.")
    print("----------------------------------------------------")
    
    ports_to_check = find_serial_ports()
    baud_rate = 9600 # Common default for SIM800L
    
    if not ports_to_check:
        print("""
[CRITICAL] No hardware serial ports found to scan.""")
        all_passed = False
        results = {}
    else:
        print(f"""
[INFO] Will check ports: {ports_to_check} at {baud_rate} baud.""")
        
        best_results = None
        for port in ports_to_check:
            results = test_gsm_on_port(port, baud_rate)
            if results and all(results.values()):
                print(f"✅ Full success on port {port}. Ending scan.")
                best_results = results
                break
            elif results and any(results.values()):
                if not best_results or sum(results.values()) > sum(best_results.values()):
                    print(f"Partial success on port {port}. Will continue scanning.")
                    best_results = results

        results = best_results # Use the best results found for the final report
        all_passed = results and all(results.values())

    print("""
==================== FINAL RESULT ====================""")
    if all_passed:
        print("✅ GSM Module test PASSED. All checks were successful.")
    else:
        print("❌ GSM Module test FAILED. See details below.")
    
    print("""
--- DETAILED CHECKS ---""")
    print(f"- Basic Communication (AT): {'PASS' if results and results.get('communication') else 'FAIL'}")
    print(f"- SIM Card Detected (AT+CPIN?): {'PASS' if results and results.get('sim_status') else 'FAIL'}")
    print(f"- Network Registration (AT+CREG?): {'PASS' if results and results.get('network_reg') else 'FAIL'}")
    print(f"- Signal Strength > 0 (AT+CSQ): {'PASS' if results and results.get('signal_strength') else 'FAIL'}")

    if not all_passed:
        print("""
--- TROUBLESHOOTING ---""")
        if not results or not results.get('communication'):
            print("- AT FAIL: Critical failure. Check wiring (TX->RX), power, and ensure module LED is blinking.")
        if not results or not results.get('sim_status'):
            print("- SIM NOT READY: Is the SIM inserted correctly? Is it activated? Is the PIN disabled?")
        if not results or not results.get('network_reg'):
            print("- NO NETWORK: Check antenna connection. It can take a few minutes to register. Try a different location.")
        if not results or not results.get('signal_strength'):
            print("- NO SIGNAL: Check antenna. Move to an area with better cell reception.")
        print("- POWER SUPPLY: The SIM800L is very power-hungry. A weak power supply is the most common point of failure.")
    print("====================================================")

if __name__ == "__main__":
    test_gsm()
