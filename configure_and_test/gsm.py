import serial
import time

# Use /dev/serial0 to automatically pick the right primary UART
SERIAL_PORT = "/dev/serial0" 
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=2)
    print(f"Connected to {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening port: {e}")
    exit()

def send_at(command, wait_time=1):
    print(f"--> {command}")
    ser.write((command + "\r\n").encode('utf-8'))
    
    # Give the module a moment to process
    time.sleep(wait_time)
    
    if ser.in_waiting:
        # 'ignore' errors in case of serial noise or non-UTF8 characters
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"<-- Response:\n{response.strip()}")
        return response
    return None

try:
    # 1. Sync baud rate (sometimes sending AT once isn't enough)
    send_at("AT")
    
    # 2. Check if SIM is ready (Ready = +CPIN: READY)
    send_at("AT+CPIN?")
    
    # 3. Signal Quality (+CSQ: <rssi>,<ber>) 10-31 is good.
    send_at("AT+CSQ")
    
    # 4. Check Network Registration (0,1 or 0,5 means registered)
    send_at("AT+CREG?")

finally:
    ser.close()
    print("Port closed.")
