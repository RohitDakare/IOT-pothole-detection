import cv2
import time
from ultralytics import YOLO

# For high accuracy on small objects, we can use SAHI-like slicing manually 
# or use the standard YOLOv8 inference with Test-Time Augmentation (TTA)
def enhanced_inference(image_path, model_path='pothole_detection_enhanced/v2_accurate/weights/best.pt'):
    """
    Run high-accuracy inference using Test-Time Augmentation (TTA) and confidence filtering.
    """
    model = YOLO(model_path)
    
    # Run inference with TTA for higher accuracy (at the cost of speed)
    # TTA flips and scales the image during inference to find hard-to-detect objects
    results = model.predict(
        source=image_path,
        conf=0.25,        # Confidence threshold
        iou=0.45,         # IOU threshold for NMS
        augment=True,     # Enable Test-Time Augmentation
        save=True         # Save the results
    )

    potholes_found = 0
    for result in results:
        boxes = result.boxes
        for box in boxes:
            potholes_found += 1
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            
            # Severity mapping based on pixel area (rough estimate)
            area = (x2 - x1) * (y2 - y1)
            severity = "Minor" if area < 5000 else "Moderate" if area < 15000 else "Critical"
            
            print(f"Detection {potholes_found}:")
            print(f"  Confidence: {conf:.4f}")
            print(f"  Estimated Severity (Visual): {severity}")
            print(f"  Bounding Box: [{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}]")

    print(f"\nTotal potholes detected: {potholes_found}")
    return results

def realtime_optimized_inference():
    """
    Example of how to run the most efficient inference for Pi 4
    """
    # Use the OpenVINO or TFLite version for real-time
    # model = YOLO('pothole_detection_enhanced/v2_accurate/weights/best_openvino_model/')
    print("For real-time usage on Raspberry Pi, use the exported OpenVINO or TFLite models.")
    print("The .pt file is best for training/validation, but OpenVINO is 3-5x faster on RPi.")

if __name__ == "__main__":
    print("--- Enhanced Inference Engine ---")
    # enhanced_inference('test_road.jpg')
    realtime_optimized_inference()
