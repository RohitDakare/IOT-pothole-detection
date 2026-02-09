import pandas as pd
import matplotlib.pyplot as plt

def plot_lidar_data():
    """
    Reads the LiDAR data from the CSV file and generates a plot.
    """
    try:
        data = pd.read_csv('raspi/lidar_data.csv')
        
        if data.empty:
            print("No data to plot.")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(data['timestamp'], data['distance'])
        plt.xlabel('Timestamp')
        plt.ylabel('Distance (cm)')
        plt.title('LiDAR Road Profile')
        plt.grid(True)
        plt.savefig('lidar_profile.png')
        print("Plot saved to lidar_profile.png")

    except FileNotFoundError:
        print("Error: lidar_data.csv not found. Run the main application to generate data.")

if __name__ == "__main__":
    plot_lidar_data()
