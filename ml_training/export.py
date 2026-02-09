from ultralytics import YOLO
import os

def export_model_optimized(model_path):
    # Load the trained model
    model = YOLO(model_path)

    print(f"Starting optimized export for {model_path}...")

    # 1. Export to TFLite (Optimized for Mobile/ESP32)
    # int8=True provides massive speedup on RPi/Edge devices
    print("Exporting to TFLite (INT8 Optimized)...")
    model.export(format='tflite', int8=True, imgsz=640)

    # 2. Export to OpenVINO (Highest Performance for Intel Macs or Raspberry Pi with OpenVINO)
    # OpenVINO is generally the fastest format for RPi 4/5 CPUs
    print("Exporting to OpenVINO...")
    model.export(format='openvino', imgsz=640)

    # 3. Export to ONNX (Standard portable format)
    print("Exporting to ONNX...")
    model.export(format='onnx', opset=12, simplify=True)

    print("--- Export Summary ---")
    print("- TFLite: Best for ESP32-CAM and basic Raspberry Pi")
    print("- OpenVINO: Best for optimized Raspberry Pi performance")
    print("- ONNX: Best for general PC/Server inference")

if __name__ == "__main__":
    # Check both potential weight locations
    weights_v2 = 'pothole_detection_enhanced/v2_accurate/weights/best.pt'
    weights_v1 = 'pothole_detection/v1/weights/best.pt'
    
    if os.path.exists(weights_v2):
        export_model_optimized(weights_v2)
    elif os.path.exists(weights_v1):
        export_model_optimized(weights_v1)
    else:
        print("Model file not found. Please run train.py first.")
