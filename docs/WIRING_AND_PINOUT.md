# Wiring and Pinout Guide

This document details the connections for the custom PCB including Raspberry Pi 4B, ESP32-CAM, sensors, and communication modules.

## Power Distribution (Critical)

| Component | Power Pin | Connected To | Notes |
|-----------|-----------|--------------|-------|
| **Raspberry Pi 4B** | 5V (Pins 2, 4) | 5V Bus | Powered via LM2596 (5V) |
| **Raspberry Pi 4B** | GND (Multiple) | GND Bus | Common Ground |
| **ESP32-CAM** | 5V | 5V Bus | 5V input |
| **NEO-6M GPS** | VCC | 5V Bus | |
| **SIM800L** | VCC | **4.0V-4.2V** | **Via Separate Regulator** (Do NOT use 5V) |
| **HC-05** | VCC | 5V Bus | |
| **TF02-Pro LiDAR** | VCC (Red) | 5V Bus | |
| **HC-SR04** | VCC | 5V Bus | |

* **5V Bus**: Derived from Battery -> LM2596 set to 5.0V.
* **SIM800L Bus**: Derived from Battery -> 2nd Regulator set to ~4.1V.
* **GND Bus**: Common to all components.

## Signal / Data Connections

### Raspberry Pi 4B GPIO Header

| Device | Signal | Pi Pin | GPIO (BCM) | Function/Notes |
|--------|--------|--------|------------|----------------|
| **NEO-6M GPS** | TX | 10 | 15 | UART0 RX (Hardware) |
| | RX | 8 | 14 | UART0 TX (Harware) |
| **SIM800L** | TXD | 38 | 20 | User defined (REQ: Voltage Divider) |
| | RXD | 36 | 16 | User defined |
| | RST | 37 | 26 | SIM800L Reset |
| **HC-05 BT** | TX | 40 | 21 | User defined |
| | RX | 35 | 19 | User defined |
| **TF02-Pro LiDAR** | TX (Green) | 32 | 12 | User defined (UART5 TX capable, check RX) |
| | RX (Yellow) | 31 | 6 | User defined |
| **HC-SR04** | TRIG | 11 | 17 | Direct |
| | ECHO | 12 | 18 | **Voltage Divider Required** (5V->3.3V) |
| **ESP32-CAM** | U0TXD | 18 | 24 | User defined |
| | U0RXD | 16 | 23 | User defined |

### Notes on Signal Logic
* **Voltage Dividers**: Essential for 5V -> 3.3V signals (HC-SR04 Echo, SIM800L TX, etc).
    * 1kΩ (Signal) + 2kΩ (GND) recommended.
* **UART Configuration**: 
    * The Raspberry Pi Hardware UARTs are typically:
        * UART0: GPIO 14/15
        * UART2: GPIO 0/1
        * UART3: GPIO 4/5
        * UART4: GPIO 8/9
        * UART5: GPIO 12/13
    * **Note**: The user-defined pins for SIM800L (20/16), HC-05 (21/19), TF02-Pro (12/6), and ESP32 (24/23) do NOT match standard Hardware UART assignments. 
    * These connections may require **Software Serial (Bit-Banging)** or specific kernel overlays if available. 
    * **TF02-Pro LiDAR** runs at 115200 baud, which is challenging for Software Serial on Pi. Verify if UART5 (GPIO 12/13) can be used instead (Move RX from Pin 31 to Pin 33).
