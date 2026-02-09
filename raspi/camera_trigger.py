"""
This module defines the ESP32Trigger class for communicating with the ESP32-CAM.
"""
import time
import serial
from soft_serial import SoftwareSerial


class ESP32Trigger:
    """A class to trigger the ESP32-CAM and handle communication."""

    def __init__(self, **kwargs):
        """
        Initializes the ESP32Trigger.

        Args:
            **kwargs: Keyword arguments for configuration.
                port (str): The serial port.
                tx (int): The TX pin for software serial.
                rx (int): The RX pin for software serial.
                baud (int): The baud rate.
                wifi_ssid (str): The WiFi SSID.
                wifi_pass (str): The WiFi password.
        """
        self.ser = None
        self._init_serial(**kwargs)

        if self.ser and kwargs.get('wifi_ssid') and kwargs.get('wifi_pass'):
            self.send_wifi_credentials(
                kwargs['wifi_ssid'], kwargs['wifi_pass']
            )

    def _init_serial(self, **kwargs):
        """Initializes the serial connection."""
        port = kwargs.get('port')
        tx = kwargs.get('tx')
        rx = kwargs.get('rx')
        baud = kwargs.get('baud', 115200)

        if port:
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
                print(f"ESP32-CAM: Connected on {port}")
                return
            except serial.SerialException:
                pass

        if not (tx and rx):
            ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]
            for p in ports:
                try:
                    self.ser = serial.Serial(p, baud, timeout=1)
                    print(f"ESP32-CAM: Connected via USB Auto-Detect on {p}")
                    return
                except serial.SerialException:
                    continue

        if tx and rx:
            print(f"ESP32-CAM: Using Software Serial on TX={tx}, RX={rx}")
            try:
                self.ser = SoftwareSerial(tx, rx, baud)
            except serial.SerialException as e:
                print(f"ESP32-CAM: SW Serial Init Failed: {e}")

        if not self.ser:
            print("ESP32-CAM: No valid connection method found.")

    def send_wifi_credentials(self, ssid, password):
        """Sends WiFi credentials to the ESP32-CAM."""
        if self.ser:
            try:
                print("Sending WiFi credentials to ESP32-CAM...")
                self.ser.write(f"ssid:{ssid}\n".encode())
                time.sleep(0.1)
                self.ser.write(f"pass:{password}\n".encode())
                time.sleep(2)  # Give time for ESP32 to connect to WiFi
            except (serial.SerialException, OSError) as e:
                print(f"ESP32 WiFi Credential Send Error: {e}")

    def trigger(self):
        """Triggers the ESP32-CAM to take a picture."""
        if self.ser:
            try:
                print("Sending CAPTURE command to ESP32...")
                self.ser.write(b'c')
            except (serial.SerialException, OSError) as e:
                print(f"ESP32 Trigger Error: {e}")
        else:
            print("ESP32 Trigger Failed: No Connection")

    def wait_for_confirmation(self, timeout=10):
        """
        Waits for an upload confirmation from the ESP32-CAM.

        Args:
            timeout (int, optional): The timeout in seconds. Defaults to 10.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        if not self.ser:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.read(
                        self.ser.in_waiting
                    ).decode(errors='ignore')
                    if "UPLOAD_SUCCESS" in response:
                        print("ESP32-CAM upload confirmation received.")
                        return True
                    if "UPLOAD_FAILED" in response:
                        print("ESP32-CAM upload failed.")
                        return False
            except (serial.SerialException, OSError):
                return False
            time.sleep(0.1)
        print("ESP32-CAM confirmation timeout.")
        return False
