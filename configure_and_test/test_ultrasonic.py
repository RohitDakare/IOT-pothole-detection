import time
import sys
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a mock for environments without RPi.GPIO
    class MockGPIO:
        BCM = 11
        IN = 10
        OUT = 11
        def setmode(self, mode): pass
        def setwarnings(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, state): pass
        def input(self, pin): return 0
    GPIO = MockGPIO()
    print("Warning: RPi.GPIO not found. Using a mock library for syntax checking.")

# --- Configuration ---
# Pin numbers are based on BCM numbering
TRIG_PIN = 17
ECHO_PIN = 18

def get_distance():
    """
    Measures distance using the HC-SR04 sensor.
    Triggers the sensor, waits for the echo, and calculates distance.
    Returns the distance in centimeters, or -1 on timeout.
    """
    # Send a 10-microsecond pulse to the TRIG pin to start the measurement
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    # --- Measure the echo pulse ---
    # The pulse start time is recorded when the ECHO pin goes high
    # The pulse end time is recorded when the ECHO pin goes low
    
    pulse_start_time = time.time()
    pulse_end_time = time.time()

    # Wait for the echo pulse to start (pin goes HIGH)
    # A timeout prevents the script from getting stuck if the sensor is disconnected
    timeout = time.time() + 0.1 # 100ms timeout
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() > timeout:
            return -1 # Timeout error
        pulse_start_time = time.time()

    # Wait for the echo pulse to end (pin goes LOW)
    timeout = time.time() + 0.1 # 100ms timeout
    while GPIO.input(ECHO_PIN) == 1:
        if time.time() > timeout:
            return -1 # Timeout error
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    
    # Calculate distance in cm:
    # Distance = (Time * Speed of Sound) / 2
    # Speed of sound is approx. 34300 cm/s
    distance = (pulse_duration * 34300) / 2
    
    return distance

def test_ultrasonic(duration=5):
    """
    Initializes GPIO and tests the ultrasonic sensor for a specified duration,
    then prints a summary of the results.
    """
    print("======================================================")
    print("=== Testing HC-SR04 Ultrasonic Sensor              ===")
    print("======================================================")
    
    try:
        # Use a try-finally block to ensure GPIO is always cleaned up on exit
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)

        print(f"  - Pins (BCM): TRIG={TRIG_PIN}, ECHO={ECHO_PIN}")
        print(f"  - Test will run for {duration} seconds.")
        print("  - Hold an object ~10-50cm in front of the sensor for testing.")
        print("------------------------------------------------------")
        
        # Ensure trigger is low to start, then wait for the sensor to settle
        GPIO.output(TRIG_PIN, False)
        print("Allowing sensor to settle for 2 seconds...")
        time.sleep(2)
        
        print("""
Starting readings...""")
        readings = []
        timeouts = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            dist = get_distance()
            if dist > 0:
                print(f"  Distance: {dist:.1f} cm")
                readings.append(dist)
            else:
                print("  Sensor timed out. Check wiring or sensor placement.")
                timeouts += 1
            time.sleep(0.5) # Wait half a second between readings

    except KeyboardInterrupt:
        print("""
Test stopped by user.""")
    except Exception as e:
        print(f"""
An unexpected error occurred: {e}""")
    
    # The result summary is printed outside the main loop
    print("""
==================== FINAL RESULT ====================""")
    if 'readings' in locals() and readings:
        avg_dist = sum(readings) / len(readings)
        print(f"✅ Ultrasonic test PASSED.")
        print(f"  - Acquired {len(readings)} valid readings (with {timeouts} timeouts).")
        print(f"  - Average distance: {avg_dist:.1f} cm")
    else:
        print("❌ Ultrasonic test FAILED. No valid readings were obtained.")
        print("""
   TROUBLESHOOTING:""")
        print("   1. WIRING: Check VCC (5V), GND, TRIG, and ECHO pin connections are secure.")
        print("   2. POWER: Ensure the Pi is providing a stable 5V to the sensor.")
        print("   3. OBSTRUCTIONS: Make sure there's an object within the sensor's range (e.g., 10-50cm).")
    print("======================================================")
    # GPIO.cleanup() is intentionally omitted here.
    # The main 'run_all_tests.sh' script is responsible for the final cleanup.

if __name__ == "__main__":
    # This allows running the script with a custom duration from the command line
    # Example: python3 test_ultrasonic.py 10
    duration_arg = 5
    if len(sys.argv) > 1:
        try:
            duration_arg = int(sys.argv[1])
        except (ValueError, IndexError):
            print(f"Invalid duration provided. Using default {duration_arg} seconds.")
            
    test_ultrasonic(duration=duration_arg)
