from ultralytics import YOLO
import os

def train_pothole_model_enhanced():
    # Load a pretrained YOLOv8n model
    # Using 'n' for efficiency, but with advanced training parameters for accuracy
    model = YOLO('yolov8n.pt')

    # Enhanced Training with Advanced Augmentation
    # These parameters are specifically tuned for road detection:
    # - mosaic: 1.0 (Stitch 4 images together to help with small objects)
    # - mixup: 0.1 (Blend images to improve robustness)
    # - blur/noise: Helps with motion blur from moving vehicle
    # - degrees: Rotation for cornering views
    results = model.train(
        data='dataset_config.yaml',
        epochs=150,           # Increased epochs for better convergence
        imgsz=640,
        patience=30,          # Early stopping to prevent overfitting
        batch=16,             # Adjust based on GPU memory
        device='cpu',         # Change to 0 for GPU
        
        # Augmentation Strategy
        mosaic=1.0,           # High mosaic for small pothole detection
        mixup=0.15,           # Improves generalization
        copy_paste=0.1,       # Helps with instance variations
        hsv_h=0.015,          # Hue variation
        hsv_s=0.7,            # Saturation variation
        hsv_v=0.4,            # Value (brightness) variation
        degrees=5.0,          # Slight rotation
        translate=0.1,        # Translation
        scale=0.5,            # Scaling
        shear=2.0,            # Shear
        perspective=0.0001,   # Perspective transform
        flipud=0.0,           # No up-down flip for road surface
        fliplr=0.5,           # Left-right flip is fine
        blur=0.1,             # Add blur for motion robustness
        
        # Optimization
        lr0=0.01,             # Initial learning rate
        lrf=0.01,             # Final learning rate factor
        momentum=0.937,
        weight_decay=0.0005,
        
        project='pothole_detection_enhanced',
        name='v2_accurate'
    )

    # Validate the model
    metrics = model.val()
    print(f"Validation mAP@50: {metrics.box.map50}")
    print(f"Validation mAP@50-95: {metrics.box.map}")

if __name__ == "__main__":
    train_pothole_model_enhanced()
