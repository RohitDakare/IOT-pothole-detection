# 🚀 LiDAR Quick Reference Card

## ✅ What Was Fixed
1. **Frame synchronization** - Now searches for header before reading
2. **Port configuration** - Changed from UART5 to UART4 (`/dev/ttyAMA4`)
3. **Header comparison** - Fixed byte comparison bug

## 📍 Correct Wiring (UART4)
```
TF02-Pro          Raspberry Pi
--------          ------------
VCC (Red)    →    5V (Pin 2 or 4)
GND (Black)  →    GND
TX (Green)   →    GPIO 9 (Pin 21)  ← UART4 RX
RX (White)   →    GPIO 8 (Pin 24)  ← UART4 TX
```

## 🧪 Test Command
```bash
cd /home/admin/main/IOT/configure_and_test
python3 test_lidar.py
```

## ▶️ Run Detection System
```bash
cd /home/admin/main/IOT/raspi
python3 main2.py
```

## 📊 Monitor Logs
```bash
tail -f /home/admin/main/IOT/logs/pothole_system.log
```

## ⚙️ Boot Config Required
Add to `/boot/config.txt`:
```
dtoverlay=uart4
enable_uart=1
```

## 🔧 Quick Fixes

**Permission denied?**
```bash
sudo chmod 666 /dev/ttyAMA4
```

**Port not found?**
```bash
ls -l /dev/ttyAMA*
# If /dev/ttyAMA4 missing, check boot config
```

**Still not working?**
1. Check wiring (TX↔RX swap?)
2. Verify 5V power
3. Check UART4 enabled in boot config
4. Try: `sudo reboot`

## 📈 Expected Results
- ✅ 95-100% valid frames
- ✅ Continuous distance readings
- ✅ Pothole detection when depth > 5cm
- ✅ No "Invalid header" errors

## 📁 Files Changed
- `raspi/sensors.py` - Frame sync
- `raspi/main2.py` - Port config
- `configure_and_test/test_lidar.py` - Test updates

---
**Status**: ✅ Ready to deploy  
**Date**: 2026-02-10
