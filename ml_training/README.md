# Enhanced Pothole Detection ML (v2 Accurate)

This folder contains the **Enhanced Edition** of the pothole detection model. It has been optimized for higher accuracy in challenging road conditions and maximum efficiency on edge hardware.

## Key Enhancements

1.  **Advanced Augmentation:** The training script now uses Mosaic, Mixup, and Blur transforms to help the model handle motion blur from the vehicle and varied lighting.
2.  **Increased Precision:** Switched to 150 epochs with early stopping and a more granular learning rate schedule.
3.  **Multi-Format Export:** 
    - **OpenVINO:** Up to 5x faster on Raspberry Pi CPU.
    - **INT8 TFLite:** Maximum efficiency for ESP32-CAM and low-memory devices.
    - **ONNX:** Standard for server-side validation.
4.  **TTA Inference:** Added Test-Time Augmentation (TTA) in `inference_enhanced.py` for maximum detection accuracy.

## Workflow

### 1. Training (Accuracy Focus)
```bash
python train.py
```
*Note: This script now includes hyperparameter tuning for road surfaces.*

### 2. Export (Efficiency Focus)
```bash
python export.py
```
This generates the `openvino` folder and `_int8.tflite` files.

### 3. Inference Comparison
- Use `inference.py` for standard speed.
- Use `inference_enhanced.py` for maximum accuracy (includes TTA).

## Optimization for Raspberry Pi
For the best results on the Raspberry Pi 4B:
1. Install OpenVINO toolkit.
2. Use the OpenVINO exported model.
3. Set `imgsz=320` in the detection script if you need >30 FPS.
