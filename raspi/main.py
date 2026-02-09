# pylint: disable=import-error, no-member, wrong-import-position
"""
Main application for the Pothole Detection System.

This script initializes and runs the pothole detection system, which uses
a variety of sensors to detect potholes, classify them using a machine
learning model, and send the data to a remote server.
"""
import sys
import time
import threading
import serial
from RPi import GPIO

# Add project root to Python path
sys.path.append('/home/admin/main/IOT')

from sensors import LiDAR, Ultrasonic, GPS
from communication import GSM
from camera_trigger import ESP32Trigger
from motors import MotorController
from soft_serial import SoftwareSerial
from sensor_ml_model.pi_inference import SensorMLInference

# --- Configuration ---
POTHOLE_THRESHOLD = 5.0  # cm
SEVERITY_LEVELS = {"Minor": (1, 3), "Moderate": (3, 7), "Critical": (7, 100)}
ESTIMATED_SPEED_CM_S = 30.0
LIDAR_BAUD_RATE = 9600

WIFI_SSID = "TP-Link_2CF7"
WIFI_PASSWORD = "Tp@16121991"


class PotholeSystem:
    """Main class for the Pothole Detection System."""

    def __init__(self):
        """Initializes the system."""
        GPIO.setmode(GPIO.BCM)
        self.running = True
        self.sensors = self._init_sensors()
        self.comms = self._init_comms()
        self.motors = MotorController()
        self.lidar_log_file = open('lidar_data.csv', 'w')
        self.lidar_log_file.write('timestamp,distance\n')
        try:
            self.ml_model = SensorMLInference(
                model_path='sensor_ml_model/pothole_sensor_model.pkl'
            )
        except Exception as e:
            print(f"Warning: Could not load ML model: {e}. Pothole classification will be skipped.")
            self.ml_model = None

    def _init_sensors(self):
        """Initializes all sensors."""
        return {
            'ultrasonic': Ultrasonic(17, 18),
            'gps': GPS(),
            'lidar': LiDAR(tx=12, rx=6, baud=LIDAR_BAUD_RATE),
        }

    def _init_comms(self):
        """Initializes all communication modules."""
        comms = {
            'gsm': GSM(tx=16, rx=20),
            'camera': ESP32Trigger(
                tx=23, rx=24, wifi_ssid=WIFI_SSID, wifi_pass=WIFI_PASSWORD
            ),
            'bluetooth': None,
        }
        print("Bluetooth: Initializing Software Serial on 19(TX), 21(RX)...")
        try:
            comms['bluetooth'] = SoftwareSerial(tx=19, rx=21, baud=9600)
            print("Bluetooth SoftSerial Started.")
        except serial.SerialException as e:
            print(f"Bluetooth Init Failed: {e}")

        if not comms['bluetooth']:
            for port in ["/dev/ttyAMA2", "/dev/ttyAMA3", "/dev/rfcomm0"]:
                try:
                    comms['bluetooth'] = serial.Serial(port, 9600, timeout=1)
                    print(f"Bluetooth connected on {port}")
                    break
                except serial.SerialException:
                    continue
        return comms

    def bluetooth_control(self):
        """Listens for bluetooth commands and controls the motors."""
        if not self.comms['bluetooth']:
            return
        while self.running:
            try:
                if self.comms['bluetooth'].in_waiting > 0:
                    cmd = self.comms['bluetooth'].read().decode().lower()
                    if cmd == 'f':
                        self.motors.forward()
                    elif cmd == 'b':
                        self.motors.backward()
                    elif cmd == 'l':
                        self.motors.left()
                    elif cmd == 'r':
                        self.motors.right()
                    elif cmd == 's':
                        self.motors.stop()
                time.sleep(0.05)
            except (serial.SerialException, UnicodeDecodeError):
                break

    def detection_loop(self):
        """The main loop for detecting potholes."""
        print("Detection loop started...")
        event_readings = []
        event_start_time = 0
        in_pothole_event = False

        while self.running:
            lidar_depth = self.sensors['lidar'].get_distance() * 100  # m to cm
            self.lidar_log_file.write(f'{time.time()},{lidar_depth}\n')

            if lidar_depth > POTHOLE_THRESHOLD:
                if not in_pothole_event:
                    in_pothole_event = True
                    event_start_time = time.time()
                event_readings.append(lidar_depth)
            elif in_pothole_event:
                in_pothole_event = False
                self._handle_pothole_event(event_readings, event_start_time)
                event_readings = []
            time.sleep(0.05)  # 20Hz sampling

    def _handle_pothole_event(self, readings, start_time):
        """Classifies and reports a pothole event."""
        duration = time.time() - start_time
        if not readings:
            return

        if not self.ml_model:
            print("Warning: ML model not loaded, skipping pothole classification.")
            return

        classification = self.ml_model.classify_event(readings, duration)

        if "pothole" in classification.lower():
            max_depth = max(readings)
            length = duration * ESTIMATED_SPEED_CM_S
            print(
                f"Pothole Confirmed! Depth: {max_depth:.1f}cm, "
                f"Length: {length:.1f}cm"
            )

            self.comms['camera'].trigger()
            coords = self.sensors['gps'].get_location()
            severity = self.calculate_severity(max_depth)

            data = {
                "latitude": coords['lat'],
                "longitude": coords['lon'],
                "depth": float(f"{max_depth:.2f}"),
                "length": float(f"{length:.2f}"),
                "width": 0.0,
                "severity": severity,
                "classification": classification,
                "timestamp": time.time(),
            }

            if coords['fixed']:
                print(f"  > Location: {coords['lat']:.5f}, {coords['lon']:.5f}")
            else:
                print("  > Warning: No GPS Fix")

            self.comms['gsm'].send_data(data)
            self.comms['camera'].wait_for_confirmation()

    def calculate_severity(self, depth):
        """Calculates the severity of a pothole based on its depth."""
        for level, (low, high) in SEVERITY_LEVELS.items():
            if low <= depth < high:
                return level
        return "Critical"

    def run(self):
        """Starts the pothole detection system."""
        bt_thread = threading.Thread(target=self.bluetooth_control)
        bt_thread.daemon = True
        bt_thread.start()
        try:
            self.detection_loop()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shuts down the system gracefully."""
        self.running = False
        self.motors.stop()
        self.sensors['gps'].stop()
        self.comms['gsm'].close()
        self.lidar_log_file.close()
        GPIO.cleanup()


if __name__ == "__main__":
    pothole_system = PotholeSystem()
    pothole_system.run()
