
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
import sqlite3
import requests
import uuid
import logging.handlers
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
import serial
from RPi import GPIO
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
        
        # Road Profile Buffering
        self.road_buffer = []
        self.session_id = str(uuid.uuid4())
        self.road_buffer_lock = threading.Lock()
        
        # Start background uploader
        threading.Thread(target=self._upload_road_profile_loop, daemon=True).start()
        self._init_local_db() # Ensure local DB is ready

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
        self.logger.info("Bluetooth control thread stopped")

    def detection_loop(self):
        """
        High-Performance 50Hz Detection Loop with Sensor Fusion.
        Target Latency: < 20ms processing time.
        """
        self.logger.info("🚀 Starting High-Speed Detection Loop (50Hz)")
        
        if not self.sensors.get('lidar'):
            self.logger.critical("LiDAR sens not available!")
            return
        
        # High-Speed Config
        SAMPLING_INTERVAL = 0.02  # 20ms = 50Hz
        
        # Rolling Buffers
        baseline_window = []
        baseline_window_size = 20
        baseline_distance = None
        
        # Event Tracking
        event_readings = []
        event_start_time = 0
        in_pothole_event = False
        loop_count = 0
        
        # Performance Monitoring
        next_loop_time = time.time()
        
        while not self._shutdown_event.is_set():
            try:
                loop_start = time.time()
                
                # 1. FAST LiDAR Read
                # We expect the sensor class to handle raw buffering
                lidar_dist_m = self.sensors['lidar'].get_distance()
                
                # If LiDAR misses, don't block, just skip frame (maintain 50Hz cadence)
                if lidar_dist_m is None:
                    # Busy wait for next slot to maintain timing precision
                    while time.time() < next_loop_time:
                         time.sleep(0.001) 
                    next_loop_time += SAMPLING_INTERVAL
                    continue

                lidar_cm = lidar_dist_m * 100
                
                # 2. Raw 3D Logging (for Dashboard Point Cloud)
                if self.config.enable_raw_lidar_logging:
                    self._log_raw_lidar(lidar_cm)

                # 3. Dynamic Baseline Tracking (The "Ground" Level)
                if not in_pothole_event:
                    baseline_window.append(lidar_cm)
                    if len(baseline_window) > baseline_window_size:
                        baseline_window.pop(0)
                    
                    if len(baseline_window) >= 10:
                        # Fast median approximation
                        sorted_window = sorted(baseline_window)
                        baseline_distance = sorted_window[len(sorted_window)//2]

                # 4. Calculate Depth
                depth = 0.0
                if baseline_distance:
                    depth = lidar_cm - baseline_distance

                # 5. POTHOLE LOGIC
                if depth > self.config.pothole_threshold:
                    if not in_pothole_event:
                        # --- START OF EVENT ---
                        in_pothole_event = True
                        event_start_time = time.time()
                        self.logger.info(f"⚡ POTHOLE TRIGGER: {depth:.1f}cm depth")
                        
                        # TRIGGER CAMERA INSTANTLY (latency critical)
                        if self.comms.get('camera'):
                             threading.Thread(target=self.comms['camera'].trigger).start()

                    event_readings.append(depth)
                
                elif in_pothole_event:
                    # --- END OF EVENT ---
                    in_pothole_event = False
                    duration = time.time() - event_start_time
                    
                    if len(event_readings) >= 2: # Min 2 samples (40ms detection duration)
                         # FUSE ULTRASONIC DATA HERE (Backup Validtion)
                         us_depth = 0
                         if self.sensors.get('ultrasonic'):
                             us_dist = self.sensors['ultrasonic'].get_distance()
                             if us_dist and baseline_distance:
                                 us_depth = us_dist - baseline_distance

                         self._handle_pothole_event(event_readings, event_start_time, us_depth_validation=us_depth)
                    
                    event_readings = []

                # 6. Precision Timing (50Hz)
                next_loop_time += SAMPLING_INTERVAL
                sleep_time = next_loop_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                time.sleep(0.05)


    def _handle_pothole_event(self, readings: List[float], start_time: float, us_depth_validation=0):
        """
        Process event and send 3D-ready data to backend.
        """
        duration = time.time() - start_time
        
        # 1. Advanced Measurement Analysis
        try:
            from pothole_measurement import PotholeAnalyzer
            analyzer = PotholeAnalyzer(
                vehicle_speed=self.config.estimated_speed,
                sensor_height=15.0,
                sampling_rate=50.0 # Updated to 50Hz
            )
            measurement = analyzer.analyze_pothole(readings, duration)
            
            max_depth = measurement.max_depth
            length = measurement.length
            width = measurement.width
            volume = measurement.volume
            confidence = measurement.confidence
            
        except ImportError:
            max_depth = max(readings)
            length = duration * self.config.estimated_speed
            width = length * 0.85
            volume = (length * width * max_depth) / 2
            confidence = 0.5

        # 2. Get Location
        coords = self._get_gps_coordinates() or {'lat': 0.0, 'lon': 0.0, 'fixed': False}

        # 3. Construct 3D Payload
        # "dimensions" object specifically for 3D dashboard section
        data = {
            "latitude": coords['lat'],
            "longitude": coords['lon'],
            "depth": round(max_depth, 2),
            "avg_depth": round(sum(readings)/len(readings), 2),
            "length": round(length, 2),
            "width": round(width, 2),
            "volume": round(volume, 2),
            "confidence": round(confidence, 2),
            "sensor_fusion": {
                "lidar_depth": round(max_depth, 2),
                "ultrasonic_depth": round(us_depth_validation, 2) if us_depth_validation else None,
                "backup_confirmed": (us_depth_validation > self.config.pothole_threshold) if us_depth_validation else False
            },
            "timestamp": datetime.now().isoformat(),
            "gps_fixed": coords['fixed'],
            "3d_view": True,
            "profile": [round(x, 1) for x in readings]  # Raw depth profile for 3D plotting
        }

        # 3a. Classification (Non-blocking)
        if self.ml_model:
             try:
                 data["classification"] = self.ml_model.classify_event(readings, duration)
             except:
                 data["classification"] = "pothole"
        else:
             data["classification"] = "pothole"

        self.logger.info(
            f"🚀 DETECTED POTHOLE!\n"
            f"   📏 Dimensions: {length:.2f}cm (L) x {width:.2f}cm (W) x {max_depth:.2f}cm (D)\n"
            f"   📦 Volume: {volume:.0f}cm³ | Fusion Verified: {data['sensor_fusion']['backup_confirmed']}"
        )

        # 4. SEND (Trigger GSM/Backend)
        if self.comms.get('gsm'):
            # Run in thread to not block next detection
            threading.Thread(target=self.comms['gsm'].send_data, args=(data,)).start()
        else:
            self.logger.warning("GSM not available, data not sent")
        
        # Camera confirmation (non-blocking)
        if self.comms.get('camera'):
            try:
                threading.Thread(
                    target=self.comms['camera'].wait_for_confirmation,
                    daemon=True
                ).start()
            except Exception as e:
                self.logger.error(f"Camera confirmation error: {e}")

    def _get_gps_coordinates(self) -> Optional[Dict[str, Any]]:
        """Get GPS coordinates with error handling."""
        if not self.sensors.get('gps'):
            # self.logger.warning("GPS sensor not available") # removed to reduce log noise
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

    def _init_local_db(self):
        """Initialize local SQLite database for raw logging."""
        try:
            conn = sqlite3.connect('lidar_log.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_lidar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    distance_cm REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to init local DB: {e}")

    def _log_raw_lidar(self, distance_cm: float):
        """Log raw LiDAR reading to local SQLite and buffer for upload."""
        ts = time.time()
        
        # 1. Local DB
        try:
            conn = sqlite3.connect('lidar_log.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO raw_lidar (timestamp, distance_cm) VALUES (?, ?)",
                (ts, distance_cm)
            )
            conn.commit()
            conn.close()
        except: pass

        # 2. Buffer for Upload
        try:
            with self.road_buffer_lock:
                # z = distance along road = (time - start_time) * estimated_speed (e.g. 5 m/s)
                # This makes the 3D map start at z=0 and grow forward
                relative_z = (ts - self.stats['start_time']) * 5.0 
                self.road_buffer.append({'x': 0.0, 'y': distance_cm, 'z': relative_z})
        except: pass

    def _upload_road_profile_loop(self):
        """Background thread to upload road profile."""
        # 1. Default Remote IP
        base_url = "http://195.35.23.26"
        
        # 2. Check Localhost (Development Mode)
        try:
            # Fast check with tiny timeout
            if requests.get("http://127.0.0.1:8000/docs", timeout=0.2).status_code == 200:
                base_url = "http://127.0.0.1:8000"
                self.logger.info("ℹ️ Local backend detected! Switching target to localhost.")
        except:
            pass
            
        url = f"{base_url}/api/road-profile"
        self.logger.info(f"📡 3D Data Upload Thread Started. Target: {url}")

        while not self._shutdown_event.is_set():
            time.sleep(1.0) # 1Hz upload
            
            batch = []
            with self.road_buffer_lock:
                if self.road_buffer:
                    batch = list(self.road_buffer)
                    self.road_buffer.clear()
            
            if batch:
                try:
                    response = requests.post(url, json={
                        "session_id": self.session_id,
                        "points": batch
                    }, timeout=2)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"⚠️ Upload failed: {response.status_code} - {response.text}")
                    # else:
                    #     self.logger.debug(f"✅ Sent {len(batch)} points")

                except requests.exceptions.ConnectionError:
                    self.logger.error(f"❌ Connection Error: Cannot reach {base_url}. Is backend running?")
                except Exception as e:
                    self.logger.error(f"❌ Upload Error: {e}")

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
