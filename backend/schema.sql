-- Database Schema for Pothole Detection System

CREATE DATABASE pothole_system;

USE pothole_system;

CREATE TABLE potholes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    depth DECIMAL(5, 2),        -- Measured in cm
    diameter DECIMAL(5, 2),     -- Measured in cm (estimated)
    height DECIMAL(5, 2),       -- Measured in cm (for bumps/heaves if any)
    severity_level ENUM('Minor', 'Moderate', 'Critical'),
    image_url VARCHAR(255),     -- Link to captured image
    status ENUM('Red', 'Yellow', 'Green') DEFAULT 'Red', -- Red=Dangerous, Green=Repaired
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    repaired_at TIMESTAMP NULL,
    repair_time_hours INT GENERATED ALWAYS AS (TIMESTAMPDIFF(HOUR, detected_at, repaired_at)) STORED
);

-- Table to track historical passes for verification
CREATE TABLE sensor_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pothole_id INT,
    pass_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    measured_depth DECIMAL(5, 2),
    FOREIGN KEY (pothole_id) REFERENCES potholes(id)
);
