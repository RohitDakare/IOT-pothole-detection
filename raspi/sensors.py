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
        Reads the distance from the LiDAR sensor.

        Returns:
            float: The distance in meters, or None if no valid data available.
        """
        if not self.ser:
            print("LiDAR Error: Serial port not initialized")
            return None
        try:
            if isinstance(self.ser, serial.Serial):
                if self.ser.in_waiting >= 9:
                    # Read 9 bytes for TF02-Pro (YY + 7 data bytes)
                    received_data = self.ser.read(9)
                    # CRITICAL FIX: Use 0x59 (hex for 'Y') instead of ord(b'Y')
                    # serial.read() returns bytes, where each byte is already an integer
                    if len(received_data) == 9 and received_data[0] == 0x59 and received_data[1] == 0x59:
                        d_low = received_data[2]
                        d_high = received_data[3]
                        self.dist = d_low + d_high * 256
                        # Return distance in meters
                        return self.dist / 100.0
                    else:
                        # Debug: Print what we actually received
                        if len(received_data) >= 2:
                            print(f"LiDAR: Invalid header - got 0x{received_data[0]:02X} 0x{received_data[1]:02X}, expected 0x59 0x59")
                else:
                    # No data available yet
                    return None
            else: # SoftwareSerial
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
