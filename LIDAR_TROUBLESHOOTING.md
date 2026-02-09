# LiDAR Pothole Detection - Troubleshooting Guide

## Issues Found and Fixed

### 🔴 Critical Issue #1: Header Byte Comparison Bug

**Location**: `raspi/sensors.py`, line 77

**Problem**: The code was checking for the header bytes incorrectly:
```python
# WRONG:
if received_data[0] == ord(b'Y') and received_data[1] == ord(b'Y'):
```

**Why it fails**:
- `serial.read()` returns a `bytes` object where each element is already an integer (0-255)
- `ord(b'Y')` is trying to get the ASCII code of a bytes object, which causes incorrect comparison
- The value should be compared to `0x59` (hex for ASCII 'Y' = 89 decimal)

**Fix Applied**:
```python
# CORRECT:
if received_data[0] == 0x59 and received_data[1] == 0x59:
```

---

### 🔴 Critical Issue #2: Return Value Handling

**Location**: `raspi/sensors.py`, `get_distance()` method

**Problem**: 
- The function returned `0` when no data was available
- In `main2.py`, line 442 checks if `lidar_depth > 5.0` cm to detect potholes
- A return value of `0` would never trigger detection
- Can't distinguish between "no data" and "actual 0cm reading"

**Fix Applied**:
- Changed to return `None` when no valid data is available
- Added proper handling in the detection loop to skip `None` values
- Added debug print statements to help diagnose issues

---

### 🔴 Critical Issue #3: Missing Error Feedback

**Location**: `raspi/sensors.py`, `get_distance()` method

**Problem**:
- When frames failed to parse, the code silently returned 0
- No way to know if the sensor was working or not

**Fix Applied**:
- Added debug print statements to show:
  - Invalid headers (what was received vs expected)
  - Incomplete data frames
  - Serial errors
  - Connection status

---

## TF02-Pro LiDAR Data Frame Format

The TF02-Pro sends 9-byte frames:

```
Byte 0-1: Header (0x59 0x59) - Always "YY"
Byte 2-3: Distance (Low, High) - Distance = Low + High * 256 (in cm)
Byte 4-5: Strength (Low, High) - Signal strength
Byte 6-7: Temperature (Low, High) - Internal temperature
Byte 8:   Checksum
```

**Example Frame**:
```
59 59 4D 01 8A 00 E2 00 0C
 |  |  |  |  |  |  |  |   |
 |  |  |  |  |  |  |  |   +-- Checksum
 |  |  |  |  |  |  +--+------ Temperature (226 = 28.25°C)
 |  |  |  |  +--+------------ Strength (138)
 |  |  +--+------------------ Distance (333 cm = 3.33 m)
 +--+------------------------ Header "YY"
```

---

## Diagnostic Steps

### Step 1: Run the Diagnostic Tool

I've created a **diagnostic script** to test the LiDAR:

```bash
cd /home/admin/main/IOT/raspi
python3 test_lidar.py
```

This will:
- Open the serial port
- Read 20 samples from the LiDAR
- Show you the raw bytes in hex and decimal
- Parse the frames and display distance, strength, temperature
- Identify if frames are valid or invalid
- Provide a summary with troubleshooting suggestions

**To test different ports**:
```bash
python3 test_lidar.py /dev/ttyS0 115200
python3 test_lidar.py /dev/ttyAMA0 115200
```

---

### Step 2: Check Your Wiring

**TF02-Pro Connections**:
```
TF02-Pro        Raspberry Pi
--------        ------------
VCC (Red)   →   5V (Pin 2 or 4)
GND (Black) →   GND (Any GND pin)
TX (Green)  →   RX (GPIO 13 / Pin 33) ← UART5 RX
RX (White)  →   TX (GPIO 12 / Pin 32) ← UART5 TX
```

**IMPORTANT**: 
- TX on LiDAR connects to RX on Pi
- RX on LiDAR connects to TX on Pi
- Make sure you're using GPIO 12/13 (UART5) as configured in `main2.py` line 69

---

### Step 3: Check UART Configuration

1. **Enable UART5**:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → Serial Port
   # - Would you like a login shell accessible over serial? → NO
   # - Would you like the serial port hardware enabled? → YES
   ```

2. **Check if UART5 is enabled**:
   ```bash
   ls -l /dev/ttyAMA*
   ```
   You should see `/dev/ttyAMA5`

3. **Check permissions**:
   ```bash
   sudo chmod 666 /dev/ttyAMA5
   ```

4. **Verify in boot config**:
   ```bash
   cat /boot/config.txt | grep uart
   ```
   Should show: `enable_uart=1`

---

### Step 4: Test with Different Baud Rates

The TF02-Pro **default** baud rate is **115200**, but some units may be configured differently:

```bash
# Test with 115200 (default)
python3 test_lidar.py /dev/ttyAMA5 115200

# Test with 9600 (alternative)
python3 test_lidar.py /dev/ttyAMA5 9600
```

---

### Step 5: Common Issues & Solutions

#### Issue: "Permission denied"
```bash
sudo chmod 666 /dev/ttyAMA5
# Or add user to dialout group:
sudo usermod -a -G dialout $USER
# Then logout and login again
```

#### Issue: "Port already in use"
```bash
# Check what's using the port:
sudo lsof /dev/ttyAMA5
# Kill the process or stop your main script first
```

#### Issue: "No data received"
- Check power (5V to LiDAR)
- Check wiring (TX/RX might be swapped)
- Try different UART ports (/dev/ttyS0, /dev/ttyAMA0, etc.)
- Check if LiDAR LED is blinking (indicates it's working)

#### Issue: "Invalid headers"
- Wrong baud rate - try 9600 or 115200
- TX/RX wires swapped
- Noisy power supply (add capacitor near LiDAR VCC/GND)

#### Issue: "Inconsistent readings"
- Software Serial is unreliable at 115200 baud
- Use hardware UART (recommended: /dev/ttyAMA5)
- Check for loose connections

---

## What Changed in Your Code

### File: `raspi/sensors.py`

**Before**:
```python
if len(received_data) == 9 and received_data[0] == ord(b'Y') and received_data[1] == ord(b'Y'):
    # Parse data...
    return self.dist / 100.0
return 0  # ← Always returned 0 on failure
```

**After**:
```python
if len(received_data) == 9 and received_data[0] == 0x59 and received_data[1] == 0x59:
    # Parse data...
    return self.dist / 100.0
else:
    if len(received_data) >= 2:
        print(f"LiDAR: Invalid header - got 0x{received_data[0]:02X} 0x{received_data[1]:02X}, expected 0x59 0x59")
return None  # ← Now returns None when no valid data
```

### File: `raspi/main2.py`

No changes needed! The code already handles `None` correctly on line 425-428:
```python
if lidar_depth_m is None:
    self.logger.warning("LiDAR returned None, skipping sample")
    time.sleep(self.config.sampling_rate)
    continue
```

---

## Next Steps

1. **Run the diagnostic tool** to see if the LiDAR is working:
   ```bash
   cd /home/admin/main/IOT/raspi
   python3 test_lidar.py
   ```

2. **Check the output** and follow the troubleshooting suggestions

3. **Once the diagnostic shows valid frames**, run your main detection script:
   ```bash
   python3 main2.py
   ```

4. **Monitor the logs**:
   ```bash
   tail -f /home/admin/main/IOT/logs/pothole_system.log
   ```

---

## Expected Output (Good LiDAR)

When working correctly, you should see:
```
TF02-Pro LiDAR Diagnostic Tool
Testing port: /dev/ttyAMA5
Baud rate: 115200
Opening serial port...
✓ Serial port opened successfully

Sample #1
  Raw bytes (hex): 59 59 4D 01 8A 00 E2 00 0C
  ✓ VALID FRAME
  Distance: 333 cm (3.33 m)
  Strength: 138
  Temperature: 28.2 °C

DIAGNOSTIC SUMMARY
Samples collected: 20
Valid frames: 20
Invalid frames: 0

✓ LiDAR IS WORKING CORRECTLY!
  Success rate: 100.0%
```

---

## Contact & Support

If the diagnostic tool shows:
- **Valid frames**: The sensor is working, restart your main detection script
- **Invalid frames**: Check wiring and baud rate
- **No data**: Check power, permissions, and port selection

Created: 2026-02-10
Updated: 2026-02-10
