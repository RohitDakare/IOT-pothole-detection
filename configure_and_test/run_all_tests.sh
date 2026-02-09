#!/bin/bash

# Main Test Runner for Smart Pothole Detection System
# This script executes all hardware diagnostic tests in sequence.
# It ensures that python3 is available and performs a final GPIO cleanup.

echo "=========================================================="
echo "   🚀 STARTING FULL SYSTEM HARDWARE DIAGNOSTICS   "
echo "=========================================================="
date
echo ""

# Function to run a python test.
# It checks for python3 and prints a standardized header/footer.
run_python_test() {
    if ! command -v python3 &> /dev/null
    then
        echo "CRITICAL ERROR: python3 could not be found. Please install it."
        exit 1
    fi
    echo "----------------------------------------------------------"
    echo "$1"
    # All test scripts are in the same directory as this runner.
    python3 "$(dirname "$0")/$2"
    echo "----------------------------------------------------------"
    echo ""
}

# 1. Raspberry Pi System Check
run_python_test "1. Checking Raspberry Pi Health & Config..." "test_raspberry_pi.py"

# 2. ESP32-CAM Trigger Test
run_python_test "2. Testing ESP32-CAM Communication..." "test_esp32_cam.py"

# 3. GPS Module Scan
run_python_test "3. Scanning for NEO-6M GPS Data..." "test_gps.py"

# 4. GSM Module Diagnostics
run_python_test "4. Running SIM800L GSM Module Diagnostics..." "test_gsm.py"

# 5. Bluetooth Connectivity
run_python_test "5. Testing HC-05 Bluetooth Connection..." "test_bluetooth.py"

# 6. Ultrasonic Sensor (Timed Test)
# The python script now handles the 5-second duration by default.
run_python_test "6. Testing HC-SR04 Ultrasonic Sensor..." "test_ultrasonic.py"

# 7. LiDAR Test (TF02-Pro)
run_python_test "7. Testing TF02-Pro LiDAR..." "test_lidar.py"

# 8. Final GPIO Cleanup
echo "----------------------------------------------------------"
echo "8. Cleaning up GPIO resources..."
# This command ensures that all GPIO channels are released, regardless of which script used them.
# It's a safe way to end the test suite.
python3 -c "try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.cleanup()
    print('GPIO Cleanup Complete.')
except ImportError:
    print('RPi.GPIO not found, skipping cleanup.')"
echo "----------------------------------------------------------"
echo ""

echo "=========================================================="
echo "✅ ALL DIAGNOSTICS COMPLETED"
echo "Check the outputs above for any 'FAILED' or 'Error' messages."
echo "=========================================================="
