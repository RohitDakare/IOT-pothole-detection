"""
This module defines the communication classes for the Pothole Detection System.
"""
import time
import json
import serial
from soft_serial import SoftwareSerial


class GSM:
    """
    A class to interact with the SIM800L GSM module.
    """

    def __init__(self, port=None, tx=None, rx=None, baud=9600, server_url="http://195.35.23.26"):
        """
        Initializes the GSM module.

        Args:
            port (str, optional): The serial port. Defaults to None.
            tx (int, optional): The TX pin for software serial. Defaults to None.
            rx (int, optional): The RX pin for software serial. Defaults to None.
            baud (int, optional): The baud rate. Defaults to 9600.
            server_url (str, optional): Backend server base URL.
        """
        self.ser = None
        self.baud = baud
        self.server_url = server_url.rstrip('/')

        if port:
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
                self.send_at("AT")
            except serial.SerialException as e:
                print(f"GSM: HW UART {port} failed: {e}")
        elif tx is not None and rx is not None:
            print(f"GSM: Using Software Serial on TX={tx}, RX={rx}")
            try:
                self.ser = SoftwareSerial(tx, rx, baud)
                self.send_at("AT")
            except serial.SerialException as e:
                print(f"GSM: SW UART failed: {e}")

        if self.ser:
            self.init_gsm()
        else:
            print("GSM: Initialization failed (No valid port or pins).")

    def init_gsm(self):
        """Initializes the GPRS connection."""
        if not self.ser:
            return
        self.send_at("AT+CFUN=1")
        time.sleep(1)
        self.send_at('AT+SAPBR=3,1,"Contype","GPRS"')
        self.send_at('AT+SAPBR=3,1,"APN","internet"')
        self.send_at("AT+SAPBR=1,1")

    def send_at(self, cmd, wait=1):
        """
        Sends an AT command to the GSM module.

        Args:
            cmd (str): The AT command to send.
            wait (int, optional): The time to wait for a response. Defaults to 1.

        Returns:
            str: The response from the GSM module.
        """
        if not self.ser:
            return ""
        try:
            if isinstance(self.ser, serial.Serial):
                self.ser.write((cmd + "\r\n").encode())
                time.sleep(wait)
                if self.ser.in_waiting:
                    return self.ser.read(self.ser.in_waiting).decode(errors='ignore')
            else:
                self.ser.write(cmd + "\r\n")
                time.sleep(wait)
                return ""
        except (serial.SerialException, OSError):
            return ""
        return ""

    def send_data(self, data):
        """
        Sends data to the backend server.

        Args:
            data (dict): The data to send.
        """
        if not self.ser:
            return
        json_data = json.dumps(data)
        self.send_at("AT+HTTPINIT")
        self.send_at("AT+HTTPPARA=\"CID\",1")
        self.send_at(f"AT+HTTPPARA=\"URL\",\"{self.server_url}/api/potholes\"")
        self.send_at("AT+HTTPPARA=\"CONTENT\",\"application/json\"")

        self.send_at(f"AT+HTTPDATA={len(json_data)},10000", wait=0.5)
        try:
            if isinstance(self.ser, serial.Serial):
                self.ser.write(json_data.encode())
            else:
                self.ser.write(json_data)

            time.sleep(1)
            self.send_at("AT+HTTPACTION=1", wait=3)
            self.send_at("AT+HTTPTERM")
        except (serial.SerialException, OSError):
            pass

    def close(self):
        """Closes the serial connection."""
        if self.ser and hasattr(self.ser, 'close'):
            self.ser.close()
