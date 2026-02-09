# pylint: disable=no-member
"""
This module defines the sensor classes for the Pothole Detection System.
"""
import time
import threading
import serial
try:
    from RPi import GPIO
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
    print("Warning: RPi.GPIO not found in raspi/sensors.py. Using a mock library.")

import adafruit_gps
from soft_serial import SoftwareSerial

GPIO.setwarnings(False)


class LiDAR:
    """
    A class to interact with the TF02-Pro LiDAR sensor.
    """

    def __init__(self, port="/dev/ttyS0", baud=115200, tx=None, rx=None):
        """
        Initializes the LiDAR sensor.

        Args:
            port (str, optional): The serial port. Defaults to "/dev/ttyS0".
            baud (int, optional): The baud rate. Defaults to 115200.
            tx (int, optional): The TX pin for software serial. Defaults to None.
            rx (int, optional): The RX pin for software serial. Defaults to None.
        """
        self.ser = None
        self.dist = 0

        if port and not (tx and rx):
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
            except serial.SerialException as e:
                print(f"LiDAR init failed on {port}: {e}")
        elif tx is not None and rx is not None:
            print(
                f"LiDAR: Using Software Serial on TX={tx}, RX={rx} "
                f"(Warning: 115200 baud on SW Serial is unstable)"
            )
            try:
                self.ser = SoftwareSerial(tx, rx, baud)
            except serial.SerialException as e:
                print(f"LiDAR SW Init failed: {e}")

    def get_distance(self):
        """
        Reads the distance from the LiDAR sensor with frame synchronization.

        Returns:
            float: The distance in meters, or None if no valid data available.
        """
        if not self.ser:
            print("LiDAR Error: Serial port not initialized")
            return None
        
        try:
            if isinstance(self.ser, serial.Serial):
                # FRAME SYNCHRONIZATION: Search for header 0x59 0x59
                # This prevents reading misaligned frames
                max_search_bytes = 100  # Prevent infinite loop
                bytes_searched = 0
                
                while bytes_searched < max_search_bytes:
                    if self.ser.in_waiting < 1:
                        return None  # No data available
                    
                    # Read one byte at a time looking for first 0x59
                    byte1 = self.ser.read(1)
                    bytes_searched += 1
                    
                    if byte1[0] == 0x59:
                        # Found first header byte, check for second
                        if self.ser.in_waiting < 1:
                            time.sleep(0.001)  # Brief wait for next byte
                        
                        if self.ser.in_waiting >= 1:
                            byte2 = self.ser.read(1)
                            bytes_searched += 1
                            
                            if byte2[0] == 0x59:
                                # Found valid header! Read remaining 7 bytes
                                if self.ser.in_waiting < 7:
                                    time.sleep(0.002)  # Wait for full frame
                                
                                if self.ser.in_waiting >= 7:
                                    remaining = self.ser.read(7)
                                    
                                    if len(remaining) == 7:
                                        # Parse distance from bytes 2-3 (now in remaining[0-1])
                                        d_low = remaining[0]
                                        d_high = remaining[1]
                                        self.dist = d_low + d_high * 256
                                        
                                        # Optional: Validate checksum (byte 8)
                                        # checksum = remaining[6]
                                        
                                        return self.dist / 100.0  # Convert cm to meters
                                    else:
                                        print(f"LiDAR: Incomplete frame - got {len(remaining)} bytes, expected 7")
                                        return None
                                else:
                                    return None  # Not enough data yet
                            # else: Second byte wasn't 0x59, continue searching
                    # else: Not a header byte, continue searching
                
                # Searched too many bytes without finding valid frame
                return None
                
            else:  # SoftwareSerial
                # Read 'Y' 'Y' bytes with timeout
                byte1 = self.ser.read(1, timeout=0.1)
                if byte1 == b'Y':
                    byte2 = self.ser.read(1, timeout=0.1)
                    if byte2 == b'Y':
                        # Read remaining 7 data bytes with timeout
                        data = self.ser.read(7, timeout=0.1)
                        if len(data) == 7:
                            d_low = data[0]
                            d_high = data[1]
                            self.dist = d_low + d_high * 256
                            return self.dist / 100.0
                        else:
                            print(f"LiDAR: Incomplete data frame - got {len(data)} bytes, expected 7")
                    else:
                        print(f"LiDAR: Invalid second header byte")
                else:
                    # No data available
                    return None
                    
        except serial.SerialException as e:
            print(f"LiDAR get_distance error: {e}")
            return None
        except Exception as e:
            print(f"LiDAR unexpected error: {e}")
            return None
        
        # No valid data received
        return None


class Ultrasonic:
    """
    A class to interact with the HC-SR04 ultrasonic sensor.
    """

    def __init__(self, trig, echo):
        """
        Initializes the ultrasonic sensor.

        Args:
            trig (int): The trigger pin.
            echo (int): The echo pin.
        """
        self.trig = trig
        self.echo = echo
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

    def get_distance(self):
        """
        Reads the distance from the ultrasonic sensor.

        Returns:
            float: The distance in centimeters.
        """
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        start_time = time.time()
        stop_time = time.time()
        timeout = time.time() + 0.1

        while GPIO.input(self.echo) == 0:
            start_time = time.time()
            if start_time > timeout:
                return 0

        while GPIO.input(self.echo) == 1:
            stop_time = time.time()
            if stop_time > timeout:
                return 0

        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2
        return distance


class GPS:
    """
    A class to interact with the NEO-6M GPS module.
    """

    def __init__(self, port=None):
        """
        Initializes the GPS module.

        Args:
            port (str, optional): The serial port. Defaults to None.
        """
        self.uart = None
        self.gps = None
        self.running = True
        self.latest_data = {'lat': 0.0, 'lon': 0.0, 'alt': 0.0, 'fixed': False}

        potential_ports = []
        if port:
            potential_ports.append(port)
        potential_ports.extend(
            ["/dev/ttyS0", "/dev/serial0", "/dev/ttyAMA0", "/dev/ttyUSB0", "/dev/ttyAMA5"]
        )

        for p in potential_ports:
            try:
                self.uart = serial.Serial(p, baudrate=9600, timeout=1)
                self.gps = adafruit_gps.GPS(self.uart, debug=False)
                self.gps.send_command(
                    b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
                )
                self.gps.send_command(b"PMTK220,1000")
                print(f"GPS initialized on {p}...")

                self.thread = threading.Thread(target=self._update_loop)
                self.thread.daemon = True
                self.thread.start()
                break
            except serial.SerialException:
                pass

        if not self.gps:
            print("Warning: GPS could not be initialized.")

    def _update_loop(self):
        """Continuously updates the GPS data in a separate thread."""
        while self.running:
            try:
                if not self.gps:
                    break
                self.gps.update()
                if self.gps.has_fix:
                    self.latest_data = {
                        'lat': self.gps.latitude,
                        'lon': self.gps.longitude,
                        'alt': self.gps.altitude_m,
                        'fixed': True,
                    }
                else:
                    self.latest_data['fixed'] = False
                time.sleep(0.1)
            except (serial.SerialException, IOError):
                time.sleep(1)

    def get_location(self):
        """
        Returns the latest GPS data.

        Returns:
            dict: A dictionary containing the latitude, longitude, altitude, and fix status.
        """
        return self.latest_data

    def stop(self):
        """Stops the GPS update thread."""
        self.running = False
