#!/bin/bash

# Updated enable_uarts.sh for User Defined Wiring
# Note: User is using custom GPIO assignments for Serial devices.
# Only UART0 (Default) is used for GPS on GPIO 14/15.
# UART2 (GPIO 0/1), UART3 (GPIO 4/5), UART4 (GPIO 8/9), UART5 (GPIO 12/13) are NOT used in hardware mode.
# Instead, Software Serial will be used on other pins.

CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

echo "Updating $CONFIG_FILE configuration..."

# 1. Enable UART0 (Primary UART for GPS on GPIO 14/15)
# This is usually enabled by default on Pi 4, but let's ensure it.
grep -q "enable_uart=1" $CONFIG_FILE || echo "enable_uart=1" | sudo tee -a $CONFIG_FILE

# 2. Disable conflicting overlays if present (optional but recommended)
# We comment them out if they exist to free up GPIOs 0-13 for general use
# sed -i 's/^dtoverlay=uart[2-5]/#dtoverlay=uart&/' $CONFIG_FILE

echo "Configuration updated for UART0."
echo "If you have changed overlays, you MUST reboot."
echo "sudo reboot"
