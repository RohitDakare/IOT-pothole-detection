import cv2
import numpy as np
from ultralytics import YOLO

def run_inference(image_path, model_path='pothole_detection/v1/weights/best.pt'):
    """
    Run inference on a single image using the trained YOLOv8 model.
    """
    # Load the model
    model = YOLO(model_path)

    # Perform detection
    results = model(image_path)

    # Process results
    for result in results:
        boxes = result.boxes  # Bounding boxes
        for box in boxes:
            # Get coordinates, confidence, and class
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            
            print(f"Detected {model.names[int(cls)]} with confidence {conf:.2f} at [{x1}, {y1}, {x2}, {y2}]")
            
            # Example: Calculate width in pixels
            width_px = x2 - x1
            print(f"Pothole pixel width: {width_px:.2f}")

    # Show the results (optional)
    # result.show() 

if __name__ == "__main__":
    # Test with an image
    # run_inference('test_pothole.jpg')
    print("Inference script ready. Update image_path to test.")
