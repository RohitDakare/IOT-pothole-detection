
# pylint: disable=import-error, no-member, wrong-import-position
"""
Main application for the Pothole Detection System.

This script initializes and runs the pothole detection system, which uses
a variety of sensors to detect potholes, classify them using a machine
learning model, and send the data to a remote server.

Optimized version with:
- Comprehensive logging
- Improved error handling
- Thread safety
- Configuration management
- Resource cleanup
"""
import sys
import time
import threading
import logging
import logging.handlers
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
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
@dataclass
class SystemConfig:
    """System configuration dataclass."""
    # Detection Parameters
    pothole_threshold: float = 5.0  # cm
    sampling_rate: float = 0.05  # seconds (20Hz)
    estimated_speed: float = 30.0  # cm/s
    
    # Severity Levels
    severity_minor: tuple = (1, 3)
    severity_moderate: tuple = (3, 7)
    severity_critical: tuple = (7, 100)
    
    # Hardware Configuration
    lidar_baud_rate: int = 115200  # Default for TF02-Pro
    bluetooth_baud_rate: int = 9600
    
    # WiFi and Server Configuration
    wifi_ssid: str = "TP-Link_2CF7"
    wifi_password: str = "Tp@16121991"
    backend_url: str = "http://195.35.23.26"
    
    # Pin Configuration
    ultrasonic_trigger: int = 17
    ultrasonic_echo: int = 18
    # Using UART4 Hardware Pins (GPIO 8/9) - Confirmed working in tests
    lidar_port: str = "/dev/ttyAMA4" 
    lidar_tx: int = 12
    lidar_rx: int = 13
    gsm_tx: int = 16
    gsm_rx: int = 20
    camera_tx: int = 23
    camera_rx: int = 24
    bluetooth_tx: int = 19
    bluetooth_rx: int = 21
    
    # Logging Configuration
    log_dir: str = "/home/admin/main/IOT/logs"
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Model Configuration
    model_path: str = 'sensor_ml_model/pothole_sensor_model.pkl'
    require_ml_model: bool = True
    require_gps_fix: bool = True
    enable_raw_lidar_logging: bool = True
    raw_lidar_db: str = "lidar_readings.db"
    
    # Bluetooth Fallback Ports
    bluetooth_fallback_ports: list = None
    
    def __post_init__(self):
        """Initialize derived attributes."""
        if self.bluetooth_fallback_ports is None:
            self.bluetooth_fallback_ports = [
                "/dev/ttyAMA2", 
                "/dev/ttyAMA3", 
                "/dev/rfcomm0"
            ]
    
    @classmethod
    def from_file(cls, config_path: str) -> 'SystemConfig':
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            return cls(**config_dict)
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        except Exception as e:
            logging.error(f"Error loading config: {e}, using defaults")
            return cls()


class LoggerSetup:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logging(config: SystemConfig) -> logging.Logger:
        """Configure logging with file rotation and console output."""
        # Create logs directory
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger('PotholeSystem')
        logger.setLevel(getattr(logging, config.log_level))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'pothole_system.log',
            maxBytes=config.log_max_bytes,
            backupCount=config.log_backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'pothole_errors.log',
            maxBytes=config.log_max_bytes,
            backupCount=config.log_backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Detection events handler
        detection_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'pothole_detections.log',
            maxBytes=config.log_max_bytes,
            backupCount=config.log_backup_count
        )
        detection_handler.setLevel(logging.INFO)
        detection_handler.setFormatter(detailed_formatter)
        detection_handler.addFilter(lambda record: 'DETECTION' in record.getMessage())
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(detection_handler)
        logger.addHandler(console_handler)
        
        return logger


class PotholeSystem:
    """Main class for the Pothole Detection System with optimizations."""

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initializes the system.
        
        Args:
            config: System configuration object
        """
        self.config = config or SystemConfig()
        self.logger = LoggerSetup.setup_logging(self.config)
        
        self.logger.info("=" * 60)
        self.logger.info("Initializing Pothole Detection System")
        self.logger.info("=" * 60)
        
        # Thread-safe shutdown flag
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'detections': 0,
            'false_positives': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Initialize GPIO
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            self.logger.info("GPIO initialized successfully")
        except Exception as e:
            self.logger.error(f"GPIO initialization failed: {e}")
            raise
        
        # Initialize components
        self.sensors = self._init_sensors()
        self.comms = self._init_comms()
        self.motors = self._init_motors()
        self.ml_model = self._init_ml_model()
        
        self.logger.info("System initialization complete")

    def _init_sensors(self) -> Dict[str, Any]:
        """Initializes all sensors with error handling."""
        self.logger.info("Initializing sensors...")
        sensors = {}
        
        try:
            sensors['ultrasonic'] = Ultrasonic(
                self.config.ultrasonic_trigger,
                self.config.ultrasonic_echo
            )
            self.logger.info("✓ Ultrasonic sensor initialized")
        except Exception as e:
            self.logger.error(f"✗ Ultrasonic sensor failed: {e}")
            sensors['ultrasonic'] = None
        
        try:
            sensors['gps'] = GPS()
            self.logger.info("✓ GPS module initialized")
        except Exception as e:
            self.logger.error(f"✗ GPS module failed: {e}")
            sensors['gps'] = None
        
        try:
            # Prioritize hardware port if defined, otherwise use Software Serial
            sensors['lidar'] = LiDAR(
                port=getattr(self.config, 'lidar_port', "/dev/ttyAMA4"),
                baud=self.config.lidar_baud_rate
            )
            self.logger.info(f"✓ LiDAR sensor initialized on {getattr(self.config, 'lidar_port', '/dev/ttyAMA4')}")
        except Exception as e:
            self.logger.error(f"✗ LiDAR hardware initialization failed: {e}. Trying Software Serial...")
            try:
                sensors['lidar'] = LiDAR(
                    tx=self.config.lidar_tx,
                    rx=self.config.lidar_rx,
                    baud=self.config.lidar_baud_rate
                )
                self.logger.info("✓ LiDAR sensor initialized via Software Serial")
            except Exception as se:
                self.logger.error(f"✗ LiDAR software initialization also failed: {se}")
                sensors['lidar'] = None
        
        return sensors

    def _init_comms(self) -> Dict[str, Any]:
        """Initializes all communication modules with fallback logic."""
        self.logger.info("Initializing communication modules...")
        comms = {}
        
        # GSM
        try:
            comms['gsm'] = GSM(
                tx=self.config.gsm_tx,
                rx=self.config.gsm_rx,
                server_url=self.config.backend_url
            )
            self.logger.info(f"✓ GSM module initialized for {self.config.backend_url}")
        except Exception as e:
            self.logger.error(f"✗ GSM module failed: {e}")
            comms['gsm'] = None
        
        # Camera
        try:
            comms['camera'] = ESP32Trigger(
                tx=self.config.camera_tx,
                rx=self.config.camera_rx,
                wifi_ssid=self.config.wifi_ssid,
                wifi_pass=self.config.wifi_password
            )
            self.logger.info("✓ Camera trigger initialized")
        except Exception as e:
            self.logger.error(f"✗ Camera trigger failed: {e}")
            comms['camera'] = None
        
        # Bluetooth with fallback
        comms['bluetooth'] = self._init_bluetooth()
        
        return comms

    def _init_bluetooth(self) -> Optional[serial.Serial]:
        """Initialize bluetooth with multiple fallback options."""
        self.logger.info("Initializing Bluetooth...")
        
        # Try SoftwareSerial first
        try:
            bt = SoftwareSerial(
                tx=self.config.bluetooth_tx,
                rx=self.config.bluetooth_rx,
                baud=self.config.bluetooth_baud_rate
            )
            self.logger.info("✓ Bluetooth initialized (SoftwareSerial)")
            return bt
        except Exception as e:
            self.logger.warning(f"SoftwareSerial failed: {e}, trying hardware ports...")
        
        # Fallback to hardware serial ports
        for port in self.config.bluetooth_fallback_ports:
            try:
                bt = serial.Serial(port, self.config.bluetooth_baud_rate, timeout=1)
                self.logger.info(f"✓ Bluetooth initialized on {port}")
                return bt
            except serial.SerialException:
                continue
        
        self.logger.warning("✗ Bluetooth initialization failed on all ports")
        return None

    def _init_motors(self) -> Optional[MotorController]:
        """Initialize motor controller."""
        try:
            motors = MotorController()
            self.logger.info("✓ Motor controller initialized")
            return motors
        except Exception as e:
            self.logger.error(f"✗ Motor controller failed: {e}")
            return None

    def _init_ml_model(self) -> Optional[SensorMLInference]:
        """Initialize ML model with configuration check."""
        self.logger.info("Loading ML model...")
        try:
            model = SensorMLInference(model_path=self.config.model_path)
            self.logger.info(f"✓ ML model loaded from {self.config.model_path}")
            return model
        except Exception as e:
            self.logger.error(f"✗ ML model loading failed: {e}")
            
            if self.config.require_ml_model:
                self.logger.critical("ML model is required but failed to load. Exiting.")
                raise
            
            self.logger.warning("ML model not loaded. Classification will be skipped.")
            return None

    def bluetooth_control(self):
        """Listens for bluetooth commands and controls the motors."""
        if not self.comms.get('bluetooth') or not self.motors:
            self.logger.warning("Bluetooth control disabled (missing bluetooth or motors)")
            return
        
        self.logger.info("Bluetooth control thread started")
        command_map = {
            'f': ('forward', self.motors.forward),
            'b': ('backward', self.motors.backward),
            'l': ('left', self.motors.left),
            'r': ('right', self.motors.right),
            's': ('stop', self.motors.stop)
        }
        
        while not self._shutdown_event.is_set():
            try:
                if self.comms['bluetooth'].in_waiting > 0:
                    cmd = self.comms['bluetooth'].read().decode().lower()
                    
                    if cmd in command_map:
                        name, action = command_map[cmd]
                        action()
                        self.logger.debug(f"Bluetooth command: {name}")
                    else:
                        self.logger.debug(f"Unknown bluetooth command: {cmd}")
                
                time.sleep(0.05)
                
            except (serial.SerialException, UnicodeDecodeError) as e:
                self.logger.error(f"Bluetooth error: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected bluetooth error: {e}")
                break
        
        self.logger.info("Bluetooth control thread stopped")

    def detection_loop(self):
        """The main loop for detecting potholes with baseline tracking."""
        self.logger.info("Detection loop started")
        
        if not self.sensors.get('lidar'):
            self.logger.critical("LiDAR sensor not available. Cannot run detection.")
            return
        
        event_readings = []
        event_start_time = 0
        in_pothole_event = False
        loop_count = 0
        
        # Baseline tracking - use rolling window to establish road surface
        baseline_window = []
        baseline_window_size = 20  # Use last 20 readings for baseline
        baseline_distance = None
        
        self.logger.info("Establishing baseline... collecting initial readings")
        
        while not self._shutdown_event.is_set():
            try:
                # Get LiDAR reading (absolute distance to surface)
                lidar_distance_m = self.sensors['lidar'].get_distance()
                
                if lidar_distance_m is None:
                    self.logger.warning("LiDAR returned None, skipping sample")
                    time.sleep(self.config.sampling_rate)
                    continue
                
                lidar_distance_cm = lidar_distance_m * 100  # m to cm
                
                # Log raw data to the secondary database for Surroundings/3D Mapping
                if self.config.enable_raw_lidar_logging:
                    self._log_raw_lidar(lidar_distance_cm)
                
                # Update baseline using rolling window (when not in pothole event)
                if not in_pothole_event:
                    baseline_window.append(lidar_distance_cm)
                    if len(baseline_window) > baseline_window_size:
                        baseline_window.pop(0)
                    
                    # Calculate baseline as minimum of window (road surface)
                    if len(baseline_window) >= 5:
                        baseline_distance = min(baseline_window)
                
                # Calculate actual depth (how much deeper than baseline)
                if baseline_distance is not None:
                    # Depth = current reading - baseline
                    # Positive depth means pothole (further from sensor)
                    depth = lidar_distance_cm - baseline_distance
                else:
                    # Still establishing baseline
                    depth = 0
                
                # Log periodic status
                loop_count += 1
                if loop_count % 200 == 0:  # Every 10 seconds at 20Hz
                    self.logger.info(
                        f"Status: Distance={lidar_distance_cm:.2f}cm, "
                        f"Baseline={baseline_distance:.2f}cm if baseline_distance else 'N/A', "
                        f"Depth={depth:.2f}cm, Events={self.stats['detections']}"
                    )
                
                # Pothole detection logic - check if depth exceeds threshold
                if depth > self.config.pothole_threshold:
                    if not in_pothole_event:
                        in_pothole_event = True
                        event_start_time = time.time()
                        self.logger.info(
                            f"Pothole event started: depth={depth:.2f}cm, "
                            f"distance={lidar_distance_cm:.2f}cm, baseline={baseline_distance:.2f}cm"
                        )
                    
                    # Store the DEPTH, not absolute distance
                    event_readings.append(depth)
                    
                elif in_pothole_event:
                    # Event ended
                    in_pothole_event = False
                    duration = time.time() - event_start_time
                    self.logger.info(
                        f"Pothole event ended: duration={duration:.2f}s, samples={len(event_readings)}"
                    )
                    
                    self._handle_pothole_event(event_readings, event_start_time)
                    event_readings = []
                
                time.sleep(self.config.sampling_rate)
                
            except KeyboardInterrupt:
                self.logger.info("Detection loop interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}", exc_info=True)
                with self._lock:
                    self.stats['errors'] += 1
                time.sleep(self.config.sampling_rate)
        
        self.logger.info("Detection loop stopped")

    def _handle_pothole_event(self, readings: List[float], start_time: float):
        """
        Classifies and reports a pothole event using advanced measurement analysis.
        
        Args:
            readings: List of depth readings (in cm)
            start_time: Event start timestamp
        """
        duration = time.time() - start_time
        
        if not readings:
            self.logger.warning("Empty readings for pothole event")
            return
        
        # Import the advanced measurement system
        try:
            from pothole_measurement import PotholeAnalyzer
            
            # Initialize analyzer with system configuration
            analyzer = PotholeAnalyzer(
                vehicle_speed=self.config.estimated_speed,
                sensor_height=15.0,  # Typical sensor height above road
                sampling_rate=1.0 / self.config.sampling_rate,  # Convert to Hz
                road_surface_threshold=self.config.pothole_threshold
            )
            
            # Perform advanced analysis
            measurement = analyzer.analyze_pothole(readings, duration)
            
            # Extract measurements
            max_depth = measurement.max_depth
            avg_depth = measurement.avg_depth
            length = measurement.length
            width = measurement.width
            volume = measurement.volume
            confidence = measurement.confidence
            
            self.logger.info(
                f"Advanced Analysis: Depth={max_depth:.2f}cm, "
                f"Length={length:.2f}cm, Width={width:.2f}cm, "
                f"Volume={volume:.2f}cm³, Confidence={confidence:.2f}"
            )
            
        except ImportError:
            self.logger.warning("Advanced measurement module not available, using simple method")
            # Fallback to simple calculation
            max_depth = max(readings)
            avg_depth = sum(readings) / len(readings)
            length = duration * self.config.estimated_speed
            width = length * 0.85
            volume = 0
            confidence = 0.5
        except Exception as e:
            self.logger.error(f"Measurement analysis failed: {e}, using simple method")
            max_depth = max(readings)
            avg_depth = sum(readings) / len(readings)
            length = duration * self.config.estimated_speed
            width = length * 0.85
            volume = 0
            confidence = 0.5
        
        # ML Classification (optional - don't block on this)
        classification = "pothole"  # Default classification
        
        if self.ml_model:
            try:
                ml_classification = self.ml_model.classify_event(readings, duration)
                self.logger.info(f"ML Classification: {ml_classification}")
                
                # Only use ML classification if it's confident (not "Unknown")
                if ml_classification and ml_classification.lower() != "unknown":
                    classification = ml_classification
                    
                    # Check if ML says it's NOT a pothole
                    if "pothole" not in classification.lower():
                        self.logger.info(f"ML rejected as pothole: {classification}")
                        with self._lock:
                            self.stats['false_positives'] += 1
                        return
                else:
                    self.logger.info("ML returned Unknown - using depth-based detection")
                    
            except Exception as e:
                self.logger.warning(f"ML classification failed: {e}, proceeding with depth-based detection")
        else:
            self.logger.debug("ML model not available, using depth-based detection only")
        
        # Confirmed pothole (either by ML or by depth threshold)
        with self._lock:
            self.stats['detections'] += 1
        
        severity = self._calculate_severity(max_depth)
        
        self.logger.info("=" * 60)
        self.logger.info(f"DETECTION #{self.stats['detections']}: POTHOLE CONFIRMED!")
        self.logger.info(f"  Severity: {severity}")
        self.logger.info(f"  Max Depth: {max_depth:.2f} cm")
        self.logger.info(f"  Avg Depth: {avg_depth:.2f} cm")
        self.logger.info(f"  Estimated Length: {length:.2f} cm")
        self.logger.info(f"  Estimated Width: {width:.2f} cm")
        self.logger.info(f"  Estimated Volume: {volume:.2f} cm³")
        self.logger.info(f"  Confidence Score: {confidence:.2f}")
        self.logger.info(f"  Classification: {classification}")
        self.logger.info("=" * 60)
        
        # Trigger camera
        if self.comms.get('camera'):
            try:
                self.comms['camera'].trigger()
                self.logger.info("Camera triggered")
            except Exception as e:
                self.logger.error(f"Camera trigger failed: {e}")
        
        # Get GPS coordinates
        coords = self._get_gps_coordinates()
        
        if coords is None:
            if self.config.require_gps_fix:
                self.logger.warning("GPS fix required but not available. Skipping upload.")
                return
            coords = {'lat': 0.0, 'lon': 0.0, 'fixed': False}
        
        # Prepare data
        data = {
            "latitude": coords['lat'],
            "longitude": coords['lon'],
            "depth": round(max_depth, 2),
            "avg_depth": round(avg_depth, 2),
            "length": round(length, 2),
            "width": round(width, 2),
            "volume": round(volume, 2),
            "confidence": round(confidence, 2),
            "severity": severity,
            "classification": classification,
            "timestamp": datetime.now().isoformat(),
            "gps_fixed": coords['fixed'],
            "sample_count": len(readings)
        }
        
        # Send data
        if self.comms.get('gsm'):
            try:
                self.comms['gsm'].send_data(data)
                self.logger.info("Data sent via GSM successfully")
            except Exception as e:
                self.logger.error(f"GSM send failed: {e}")
        else:
            self.logger.warning("GSM not available, data not sent")
        
        # Wait for camera confirmation
        if self.comms.get('camera'):
            try:
                # Use threading to avoid blocking detection
                threading.Thread(
                    target=self.comms['camera'].wait_for_confirmation,
                    daemon=True
                ).start()
            except Exception as e:
                self.logger.error(f"Camera confirmation error: {e}")

    def _get_gps_coordinates(self) -> Optional[Dict[str, Any]]:
        """Get GPS coordinates with error handling."""
        if not self.sensors.get('gps'):
            self.logger.warning("GPS sensor not available")
            return None
        
        try:
            coords = self.sensors['gps'].get_location()
            
            if coords['fixed']:
                self.logger.info(f"GPS: {coords['lat']:.6f}, {coords['lon']:.6f}")
            else:
                self.logger.warning("GPS fix not available")
            
            return coords
            
        except Exception as e:
            self.logger.error(f"GPS error: {e}")
            return None

    def _calculate_severity(self, depth: float) -> str:
        """
        Calculates the severity of a pothole based on its depth.
        
        Args:
            depth: Pothole depth in cm
            
        Returns:
            Severity level string
        """
        if self.config.severity_minor[0] <= depth < self.config.severity_minor[1]:
            return "Minor"
        elif self.config.severity_moderate[0] <= depth < self.config.severity_moderate[1]:
            return "Moderate"
        else:
            return "Critical"

    def _log_statistics(self):
        """Log system statistics."""
        runtime = time.time() - self.stats['start_time']
        hours = runtime / 3600
        
        self.logger.info("=" * 60)
        self.logger.info("SYSTEM STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Runtime: {runtime/3600:.2f} hours")
        self.logger.info(f"Potholes Detected: {self.stats['detections']}")
        self.logger.info(f"False Positives: {self.stats['false_positives']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Detection Rate: {self.stats['detections']/hours:.2f} per hour")
        self.logger.info("=" * 60)

    def _log_raw_lidar(self, depth):
        """Saves a single point to the secondary high-speed database."""
        try:
            if not hasattr(self, '_raw_db_conn'):
                self._raw_db_conn = sqlite3.connect(self.config.raw_lidar_db, check_same_thread=False)
                self._raw_db_cursor = self._raw_db_conn.cursor()
                self._raw_db_cursor.execute("CREATE TABLE IF NOT EXISTS raw_data (timestamp REAL, depth REAL)")
            
            self._raw_db_cursor.execute("INSERT INTO raw_data VALUES (?, ?)", (time.time(), depth))
            self._raw_db_conn.commit()
        except: pass

    def run(self):
        """Starts the pothole detection system with proper thread management."""
        self.logger.info("Starting pothole detection system...")
        
        # Start bluetooth control thread
        bt_thread = threading.Thread(
            target=self.bluetooth_control,
            name="BluetoothControl",
            daemon=True
        )
        bt_thread.start()
        
        try:
            # Run main detection loop
            self.detection_loop()
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """Shuts down the system gracefully with proper cleanup."""
        self.logger.info("Initiating system shutdown...")
        
        # Signal shutdown to all threads
        self._shutdown_event.set()
        
        # Log final statistics
        self._log_statistics()
        
        # Stop motors
        if self.motors:
            try:
                self.motors.stop()
                self.logger.info("Motors stopped")
            except Exception as e:
                self.logger.error(f"Error stopping motors: {e}")
        
        # Stop GPS
        if self.sensors.get('gps'):
            try:
                self.sensors['gps'].stop()
                self.logger.info("GPS stopped")
            except Exception as e:
                self.logger.error(f"Error stopping GPS: {e}")
        
        # Close GSM
        if self.comms.get('gsm'):
            try:
                self.comms['gsm'].close()
                self.logger.info("GSM closed")
            except Exception as e:
                self.logger.error(f"Error closing GSM: {e}")
        
        # Close Bluetooth
        if self.comms.get('bluetooth'):
            try:
                self.comms['bluetooth'].close()
                self.logger.info("Bluetooth closed")
            except Exception as e:
                self.logger.error(f"Error closing Bluetooth: {e}")
        
        # Cleanup GPIO
        try:
            GPIO.cleanup()
            self.logger.info("GPIO cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up GPIO: {e}")
        
        self.logger.info("Shutdown complete")
        self.logger.info("=" * 60)


if __name__ == "__main__":
    # Load configuration
    config_path = "/home/admin/main/IOT/config.json"
    config = SystemConfig.from_file(config_path)
    
    # Create and run system
    try:
        pothole_system = PotholeSystem(config)
        pothole_system.run()
    except Exception as e:
        logging.critical(f"Failed to start system: {e}", exc_info=True)
        sys.exit(1)
