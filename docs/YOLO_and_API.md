# YOLO Integration & API Structure

## YOLO Integration for Pothole Detection

To enhance depth sensor readings, YOLO (You Only Look Once) can be used to visually confirm potholes and estimate their dimensions.

### Steps:
1. **Dataset Collection**: 
   - Use the ESP32-CAM to collect images of potholes from different angles and depths.
   - Annotate images using tools like LabelImg or Roboflow (Classes: `pothole`, `crack`).
2. **Model Training**:
   - Use YOLOv8 (efficient for edge devices).
   - Train on the collected dataset.
   - Export to `.onnx` or `.tflite` format for optimized performance on Raspberry Pi.
3. **Inference Logic**:
   - The Raspberry Pi runs a Python script using `opencv` and `ultralytics`.
   - When a pothole is detected by sensors, the image frame is passed to the YOLO model.
   - Output: Bounding box coordinates (used to estimate diameter) and confidence score.
4. **3D Mapping**:
   - Combine LiDAR point data with YOLO bounding boxes to create a 3D volumetric estimate of the pothole.

---

## API Documentation

### 1. Register Pothole
**Endpoint**: `POST /api/potholes`
**Payload**:
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "depth": 8.5,
  "severity": "Critical"
}
```

### 2. Upload Image
**Endpoint**: `POST /api/upload_image`
**Payload**: Multipart Form Data (Image file linked to a pothole ID)

### 3. Update Status (Repaired)
**Endpoint**: `PATCH /api/potholes/{id}/status`
**Payload**:
```json
{
  "status": "Green",
  "repaired_at": "2023-10-27T10:00:00Z"
}
```

### 4. Optimal Path Analysis (Optional)
**Endpoint**: `GET /api/path/optimal`
**Description**: Returns a sorted list of potholes based on severity and proximity using a TSP (Traveling Salesman Problem) algorithm or Dijkstra.
