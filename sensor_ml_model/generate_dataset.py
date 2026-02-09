import pandas as pd
import numpy as np
import random

def generate_sensor_data(n_samples=500):
    """
    Generates synthetic sensor data for classical ML training.
    Features are derived from TF02 Pro LiDAR and Vehicle Speed.
    """
    data = []
    classes = ["Normal Road", "Minor Pothole", "Major Pothole", "Speed Bump"]

    for _ in range(n_samples):
        cls = random.choices(classes, weights=[0.4, 0.3, 0.2, 0.1])[0]
        
        if cls == "Normal Road":
            depth_mean = random.uniform(0, 1.5)
            depth_max = random.uniform(1.5, 3.0)
            depth_std = random.uniform(0.1, 0.5)
            duration = random.uniform(0.1, 0.3)
        elif cls == "Minor Pothole":
            depth_mean = random.uniform(4, 6)
            depth_max = random.uniform(6, 8)
            depth_std = random.uniform(1.0, 2.5)
            duration = random.uniform(0.3, 0.8)
        elif cls == "Major Pothole":
            depth_mean = random.uniform(8, 15)
            depth_max = random.uniform(15, 25)
            depth_std = random.uniform(3.0, 7.0)
            duration = random.uniform(0.8, 2.0)
        elif cls == "Speed Bump":
            depth_mean = random.uniform(-5, -2) # Negative depth means surface came closer
            depth_max = random.uniform(-6, -4)
            depth_std = random.uniform(0.5, 1.5)
            duration = random.uniform(1.0, 2.5)

        data.append([depth_mean, depth_max, depth_std, duration, cls])

    df = pd.DataFrame(data, columns=['depth_mean', 'depth_max', 'depth_std', 'duration', 'label'])
    df.to_csv('sensor_pothole_data.csv', index=False)
    print("Synthetic dataset 'sensor_pothole_data.csv' created.")

if __name__ == "__main__":
    generate_sensor_data()
