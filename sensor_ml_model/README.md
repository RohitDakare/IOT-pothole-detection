# Classical Machine Learning for Pothole Detection

This folder contains a **Classical ML** pipeline that uses tabular sensor data (from LiDAR/Ultrasonic) rather than deep learning images. This is much more efficient for the Raspberry Pi CPU.

## Why Classical ML?
- **Lightweight:** Runs in microseconds on a Raspberry Pi.
- **Accurate:** Uses physical measurements (depth, duration, variance) instead of visual pixels.
- **Explainable:** You can see exactly which feature (like `depth_max`) led to the classification.

## Feature Engineering
The model uses 4 key features derived from the **TF02 Pro LiDAR**:
1. `depth_mean`: Average depth of the Road anomaly.
2. `depth_max`: The deepest point detected.
3. `depth_std`: The standard deviation (indicates surface roughness).
4. `duration`: How long the car was over the anomaly (indicates length).

## Workflow

### 1. Requirements
```bash
pip install scikit-learn pandas joblib numpy
```

### 2. Prepare Data
Run the generator to create an initial training set:
```bash
python generate_dataset.py
```

### 3. Train Model
Train the **Random Forest** classifier:
```bash
python train_ml.py
```
This will save a file named `pothole_sensor_model.pkl`.

### 4. Deploy on Pi
Use `pi_inference.py` inside your main robot loop to classify potholes in real-time based on the LiDAR data stream.
