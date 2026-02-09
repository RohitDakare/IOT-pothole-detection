import os
import subprocess
import glob

def run_command(command):
    """Runs a shell command and returns its output, handling common errors."""
    try:
        # Using a timeout is safer in case a command hangs
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"ERROR: Command failed with code {result.returncode}. STDERR: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 5 seconds."
    except FileNotFoundError:
        return "ERROR: Command not found. Is it in the system's PATH?"
    except Exception as e:
        return f"ERROR: An unexpected exception occurred: {e}"

def get_boot_config():
    """Reads the contents of the boot config file, checking standard locations."""
    # Newer Pi OS versions use /boot/firmware/config.txt
    config_path = "/boot/firmware/config.txt"
    if not os.path.exists(config_path):
        config_path = "/boot/config.txt"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return f.read()
        except IOError as e:
            return f"Error reading config file '{config_path}': {e}"
    return "Boot configuration file not found at standard locations."

def test_pi_system():
    print("======================================================")
    print("=== Raspberry Pi System Health & UART Diagnostics  ===")
    print("======================================================")

    # 1. System Information
    print("""
--- [1] System Information ---""")
    print(f"Hostname: {run_command('hostname')}")
    os_pretty_name = run_command("""grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"'""")
    print(f"OS Version: {os_pretty_name}")
    print(f"CPU Temp: {run_command('vcgencmd measure_temp')}")
    print(f"Voltage: {run_command('vcgencmd measure_volts')}")
    throttled_status = run_command('vcgencmd get_throttled')
    print(f"Throttled Status: {throttled_status}")
    if throttled_status != 'throttled=0x0':
        print("  - ❗ WARNING: System is or has been throttled! This can cause instability. Check your power supply and cooling.")
    else:
        print("  - ✅ System voltage and temperature appear OK ('0x0').")


    # 2. Disk Space
    print("""
--- [2] Disk Space (Root Filesystem) ---""")
    df_output = run_command("df -h / | tail -n 1")
    print(f"Disk Usage: {df_output}")
    try:
        use_percent = int(df_output.split()[-2][:-1])
        if use_percent > 90:
            print(f"  - ❗ WARNING: Disk space is over 90% full! This may cause errors.")
        else:
            print(f"  - ✅ Disk space is sufficient ({use_percent}% used).")
    except (ValueError, IndexError):
        print("  - Could not parse disk space percentage.")


    # 3. GPIO Library
    print("""
--- [3] GPIO Library Check ---""")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        print("✅ SUCCESS: RPi.GPIO library imported and initialized successfully in BCM mode.")
        # Cleanup is omitted here; the main test runner script will handle it.
    except Exception as e:
        print(f"❌ FAILED: Could not initialize RPi.GPIO library. Error: {e}")
        print("   Run 'pip install RPi.GPIO' or ensure you are running on a Raspberry Pi.")

    # 4. UART Diagnostics
    print("""
--- [4] UART Port & Configuration Diagnostics ---""")
    boot_config = get_boot_config()
    
    print("""
[A] Checking Boot Config for enabled UARTs...""")
    if "Error" in boot_config or "not found" in boot_config:
        print(f"  - {boot_config}")
    else:
        # Check for primary UART setting
        if "enable_uart=1" in boot_config:
            print("  - ✅ 'enable_uart=1' is present (Enables primary UART).")
        else:
            print("  - ❌ 'enable_uart=1' is MISSING (Primary UART may be disabled).")
        # Check for overlays for other hardware UARTs
        for i in range(2, 6):
            if f'dtoverlay=uart{i}' in boot_config:
                print(f"  - ✅ 'dtoverlay=uart{i}' is present (UART{i} is enabled).")

    print("""
[B] Finding available /dev/tty* serial ports...""")
    serial_ports = sorted(glob.glob("/dev/ttyS*") + glob.glob("/dev/ttyAMA*") + glob.glob("/dev/ttyUSB*"))
    if serial_ports:
        for port in serial_ports:
            print(f"  - Found: {port}")
    else:
        print("  - ❌ No /dev/ttyS*, /dev/ttyAMA*, or /dev/ttyUSB* ports found.")

    print("""
[C] Checking primary UART alias 'serial0'...""")
    serial0_path = "/dev/serial0"
    if os.path.exists(serial0_path):
        real_path = os.path.realpath(serial0_path)
        print(f"  - ✅ /dev/serial0 exists and points to -> {real_path}")
        if "ttyS0" in real_path:
            print("     - This typically means Bluetooth is DISABLED, giving UART0 to GPIO 14/15.")
        elif "ttyAMA0" in real_path:
            print("     - This typically means Bluetooth is ENABLED, and primary UART is on ttyAMA0.")
    else:
        print("  - ❌ /dev/serial0 alias not found. Primary UART may not be configured correctly.")

    print("""
--- Diagnostics Complete ---""")

if __name__ == "__main__":
    test_pi_system()
