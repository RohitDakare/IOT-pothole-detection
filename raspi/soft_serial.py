import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a mock for environments without RPi.GPIO
    class MockGPIO:
        HIGH = 1
        LOW = 0
        BCM = 11
        IN = 10
        OUT = 11
        def setmode(self, mode): pass
        def setwarnings(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, state): pass
        def input(self, pin): return 0
    GPIO = MockGPIO()
    print("Warning: RPi.GPIO not found in raspi/soft_serial.py. Using a mock library.")

class SoftwareSerial:
    """
    Software Serial implementation for pins that do not support hardware UART.
    Note: Standard RPi.GPIO is slow. For higher baud rates (>=9600), this is unreliable.
    pigpio is recommended for robust software serial, but this serves as a fallback.
    """
    def __init__(self, tx, rx, baud=9600):
        self.tx = tx
        self.rx = rx
        self.baud = baud
        self.bit_time = 1.0 / baud
        
        GPIO.setup(self.tx, GPIO.OUT)
        GPIO.output(self.tx, GPIO.HIGH) # Idle High
        GPIO.setup(self.rx, GPIO.IN)
        
    def write(self, data):
        """Blocking bit-bang write"""
        if isinstance(data, str):
            data = data.encode()
            
        for byte in data:
            # Start bit (Low)
            GPIO.output(self.tx, GPIO.LOW)
            time.sleep(self.bit_time)
            
            # Data bits (LSB first)
            val = byte
            for _ in range(8):
                bit = val & 1
                GPIO.output(self.tx, bit)
                time.sleep(self.bit_time)
                val >>= 1
                
            # Stop bit (High)
            GPIO.output(self.tx, GPIO.HIGH)
            time.sleep(self.bit_time)
            
    def read(self, count=1, timeout=1):
        """
        Blocking bit-bang read with timeout.
        WARNING: This consumes 100% CPU waiting for start bit and is timing sensitive.
        """
        data = b''
        start_time = time.time()
        for _ in range(count):
            # Wait for start bit (Low) with timeout
            while GPIO.input(self.rx) == GPIO.HIGH:
                if time.time() - start_time > timeout:
                    return b'' # Timeout
                pass
            
            # Align to end of start bit.
            # Simple approach: Wait 1.5 bit times to sample first data bit
            time.sleep(self.bit_time * 1.5)
            
            val = 0
            for i in range(8):
                bit = GPIO.input(self.rx)
                val |= (bit << i)
                time.sleep(self.bit_time)
            
            # Stop bit
            time.sleep(self.bit_time) 
            data += bytes([val])
            
        return data
    @property
    def in_waiting(self):
        # We cannot easily check in_waiting without buffering in a thread/interrupt.
        # Check if RX line is Low (Start bit)?
        return 0 if GPIO.input(self.rx) == GPIO.HIGH else 1

    def close(self):
        pass
