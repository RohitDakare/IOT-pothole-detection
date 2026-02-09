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
grep -q "enable_uart=1" $CONFIG_FILE || echo "enable_uart=1" | sudo tee -a $CONFIG_FILE

# 2. Enable UART5 (Hardware UART for LiDAR on GPIO 12/13)
# This is much more stable than Software Serial
grep -q "dtoverlay=uart5" $CONFIG_FILE || echo "dtoverlay=uart5" | sudo tee -a $CONFIG_FILE

echo "Configuration updated for UART0 and UART5."
echo "If you have changed overlays, you MUST reboot for changes to take effect."
echo "sudo reboot"
