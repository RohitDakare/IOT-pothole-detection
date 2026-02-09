#!/usr/bin/env python3
"""
LiDAR Diagnostic Tool for TF02-Pro
This script helps diagnose LiDAR connection issues
"""

import serial
import time
import sys

def test_lidar_connection(port="/dev/ttyAMA5", baud=115200):
    """
    Test LiDAR connection and data reception
    """
    print("=" * 60)
    print("TF02-Pro LiDAR Diagnostic Tool")
    print("=" * 60)
    print(f"Testing port: {port}")
    print(f"Baud rate: {baud}")
    print("-" * 60)
    
    try:
        # Try to open the serial port
        print("Opening serial port...")
        ser = serial.Serial(port, baud, timeout=1)
        print(f"✓ Serial port opened successfully")
        print(f"  Port is open: {ser.is_open}")
        time.sleep(0.5)
        
        # Check for data
        print("\nWaiting for data...")
        samples_collected = 0
        valid_frames = 0
        invalid_frames = 0
        start_time = time.time()
        
        while samples_collected < 20 and (time.time() - start_time) < 10:
            if ser.in_waiting >= 9:
                samples_collected += 1
                data = ser.read(9)
                
                # Display raw bytes
                hex_str = ' '.join([f'{b:02X}' for b in data])
                print(f"\nSample #{samples_collected}")
                print(f"  Raw bytes (hex): {hex_str}")
                print(f"  Raw bytes (dec): {' '.join([str(b) for b in data])}")
                
                # Check header
                if data[0] == 0x59 and data[1] == 0x59:
                    # Valid frame
                    valid_frames += 1
                    d_low = data[2]
                    d_high = data[3]
                    distance_cm = d_low + d_high * 256
                    
                    strength_low = data[4]
                    strength_high = data[5]
                    strength = strength_low + strength_high * 256
                    
                    temp_low = data[6]
                    temp_high = data[7]
                    temp = temp_low + temp_high * 256
                    temp_c = (temp / 8.0) - 256
                    
                    checksum = data[8]
                    
                    print(f"  ✓ VALID FRAME")
                    print(f"  Distance: {distance_cm} cm ({distance_cm/100:.2f} m)")
                    print(f"  Strength: {strength}")
                    print(f"  Temperature: {temp_c:.1f} °C")
                    print(f"  Checksum: 0x{checksum:02X}")
                    
                else:
                    invalid_frames += 1
                    print(f"  ✗ INVALID HEADER")
                    print(f"    Expected: 0x59 0x59")
                    print(f"    Got:      0x{data[0]:02X} 0x{data[1]:02X}")
                
                time.sleep(0.1)
            else:
                # No data available
                time.sleep(0.05)
        
        # Summary
        print("\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 60)
        print(f"Samples collected: {samples_collected}")
        print(f"Valid frames: {valid_frames}")
        print(f"Invalid frames: {invalid_frames}")
        
        if valid_frames > 0:
            print("\n✓ LiDAR IS WORKING CORRECTLY!")
            print("  The sensor is sending valid data.")
            success_rate = (valid_frames / samples_collected * 100) if samples_collected > 0 else 0
            print(f"  Success rate: {success_rate:.1f}%")
        elif samples_collected > 0:
            print("\n✗ LiDAR IS SENDING DATA BUT FRAMES ARE INVALID")
            print("  Possible issues:")
            print("  1. Wrong baud rate (try 9600 instead of 115200)")
            print("  2. Wiring issue (TX/RX swapped)")
            print("  3. Sensor malfunction")
        else:
            print("\n✗ NO DATA RECEIVED FROM LIDAR")
            print("  Possible issues:")
            print("  1. Wrong serial port (check /dev/ttyAMA5, /dev/ttyS0, etc.)")
            print("  2. Sensor not powered")
            print("  3. Wiring issue (disconnected TX/RX)")
            print("  4. Wrong baud rate")
        
        print("=" * 60)
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"\n✗ SERIAL PORT ERROR: {e}")
        print("\nPossible issues:")
        print("  1. Port doesn't exist or is already in use")
        print("  2. Permission denied (try: sudo chmod 666 /dev/ttyAMA5)")
        print("  3. Wrong port specified")
        print("\nAvailable serial ports:")
        import glob
        ports = glob.glob('/dev/tty*')
        for p in sorted(ports):
            if 'AMA' in p or 'USB' in p or 'ttyS' in p:
                print(f"  - {p}")
        return False
    
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        return False
    
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return valid_frames > 0


if __name__ == "__main__":
    # Allow user to specify port and baud rate
    port = "/dev/ttyAMA5"
    baud = 115200
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    if len(sys.argv) > 2:
        baud = int(sys.argv[2])
    
    print(f"\nUsage: python3 {sys.argv[0]} [port] [baud_rate]")
    print(f"Example: python3 {sys.argv[0]} /dev/ttyS0 115200\n")
    
    success = test_lidar_connection(port, baud)
    sys.exit(0 if success else 1)
