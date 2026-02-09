#!/usr/bin/env python3
"""
Pothole Measurement Calibration and Testing Tool

This script helps calibrate and test the pothole measurement system.
It can:
1. Calibrate sensor height and baseline
2. Test measurement accuracy with known potholes
3. Visualize measurement results
4. Generate calibration reports

Usage:
    python3 calibrate_measurement.py --mode [calibrate|test|demo]
"""

import sys
import time
import argparse
from typing import List, Tuple
import json

# Add raspi to path
sys.path.insert(0, '/home/admin/main/IOT/raspi')

try:
    from sensors import LiDAR
    from pothole_measurement import PotholeAnalyzer, measure_pothole
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


class MeasurementCalibrator:
    """Calibration tool for pothole measurement system."""
    
    def __init__(self, lidar_port="/dev/ttyAMA4", baud=115200):
        """Initialize calibrator with LiDAR sensor."""
        print("Initializing LiDAR sensor...")
        try:
            self.lidar = LiDAR(port=lidar_port, baud=baud)
            if not self.lidar.ser or not self.lidar.ser.is_open:
                raise Exception("LiDAR port not open")
            print(f"✓ LiDAR initialized on {lidar_port}")
        except Exception as e:
            print(f"✗ Failed to initialize LiDAR: {e}")
            sys.exit(1)
    
    def measure_baseline(self, duration=5.0, samples=100):
        """
        Measure baseline road surface distance.
        
        Args:
            duration: Measurement duration (seconds)
            samples: Number of samples to collect
            
        Returns:
            Tuple of (mean, std_dev, min, max)
        """
        print(f"\n{'='*60}")
        print("BASELINE CALIBRATION")
        print(f"{'='*60}")
        print(f"Place sensor over FLAT ROAD SURFACE")
        print(f"Collecting {samples} samples over {duration:.1f} seconds...")
        print("Press Ctrl+C to stop early\n")
        
        readings = []
        start_time = time.time()
        
        try:
            while len(readings) < samples and (time.time() - start_time) < duration:
                dist = self.lidar.get_distance()
                if dist is not None and dist > 0:
                    dist_cm = dist * 100  # Convert to cm
                    readings.append(dist_cm)
                    
                    if len(readings) % 10 == 0:
                        print(f"  Sample {len(readings)}: {dist_cm:.2f} cm")
                
                time.sleep(0.05)  # 20Hz
        
        except KeyboardInterrupt:
            print("\nMeasurement stopped by user")
        
        if len(readings) < 10:
            print("✗ Insufficient samples collected")
            return None
        
        # Calculate statistics
        import numpy as np
        mean = np.mean(readings)
        std = np.std(readings)
        minimum = np.min(readings)
        maximum = np.max(readings)
        
        print(f"\n{'='*60}")
        print("BASELINE RESULTS")
        print(f"{'='*60}")
        print(f"Samples collected: {len(readings)}")
        print(f"Mean distance:     {mean:.2f} cm")
        print(f"Std deviation:     {std:.2f} cm")
        print(f"Min distance:      {minimum:.2f} cm")
        print(f"Max distance:      {maximum:.2f} cm")
        print(f"{'='*60}")
        
        # Save calibration
        calibration = {
            'baseline_mean': mean,
            'baseline_std': std,
            'baseline_min': minimum,
            'baseline_max': maximum,
            'sample_count': len(readings),
            'timestamp': time.time()
        }
        
        with open('calibration.json', 'w') as f:
            json.dump(calibration, f, indent=2)
        
        print("✓ Calibration saved to calibration.json")
        
        return (mean, std, minimum, maximum)
    
    def test_known_pothole(
        self,
        expected_depth: float,
        expected_length: float,
        vehicle_speed: float = 30.0
    ):
        """
        Test measurement accuracy with a known pothole.
        
        Args:
            expected_depth: Known pothole depth (cm)
            expected_length: Known pothole length (cm)
            vehicle_speed: Vehicle speed (cm/s)
        """
        print(f"\n{'='*60}")
        print("KNOWN POTHOLE TEST")
        print(f"{'='*60}")
        print(f"Expected Depth:  {expected_depth:.2f} cm")
        print(f"Expected Length: {expected_length:.2f} cm")
        print(f"Vehicle Speed:   {vehicle_speed:.2f} cm/s")
        print("\nMove sensor over pothole at constant speed...")
        print("Press Ctrl+C when done\n")
        
        readings = []
        start_time = time.time()
        
        try:
            while True:
                dist = self.lidar.get_distance()
                if dist is not None and dist > 0:
                    dist_cm = dist * 100
                    readings.append(dist_cm)
                    
                    if len(readings) % 10 == 0:
                        print(f"  Sample {len(readings)}: {dist_cm:.2f} cm")
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\nMeasurement complete")
        
        duration = time.time() - start_time
        
        if len(readings) < 5:
            print("✗ Insufficient samples for analysis")
            return
        
        # Analyze pothole
        result = measure_pothole(readings, duration, vehicle_speed)
        
        # Calculate errors
        depth_error = abs(result['max_depth'] - expected_depth)
        depth_error_pct = (depth_error / expected_depth * 100) if expected_depth > 0 else 0
        
        length_error = abs(result['length'] - expected_length)
        length_error_pct = (length_error / expected_length * 100) if expected_length > 0 else 0
        
        print(f"\n{'='*60}")
        print("MEASUREMENT RESULTS")
        print(f"{'='*60}")
        print(f"Measured Depth:    {result['max_depth']:.2f} cm (expected: {expected_depth:.2f} cm)")
        print(f"  Error:           {depth_error:.2f} cm ({depth_error_pct:.1f}%)")
        print(f"\nMeasured Length:   {result['length']:.2f} cm (expected: {expected_length:.2f} cm)")
        print(f"  Error:           {length_error:.2f} cm ({length_error_pct:.1f}%)")
        print(f"\nMeasured Width:    {result['width']:.2f} cm")
        print(f"Measured Volume:   {result['volume']:.2f} cm³")
        print(f"Confidence:        {result['confidence']:.2f}")
        print(f"Samples:           {result['sample_count']}")
        print(f"{'='*60}")
        
        # Accuracy assessment
        print("\nACCURACY ASSESSMENT:")
        if depth_error_pct < 10:
            print("  Depth:  ✓ Excellent (<10% error)")
        elif depth_error_pct < 20:
            print("  Depth:  ⚠ Good (10-20% error)")
        else:
            print("  Depth:  ✗ Poor (>20% error)")
        
        if length_error_pct < 15:
            print("  Length: ✓ Excellent (<15% error)")
        elif length_error_pct < 30:
            print("  Length: ⚠ Good (15-30% error)")
        else:
            print("  Length: ✗ Poor (>30% error)")
    
    def demo_mode(self, duration=30.0):
        """
        Continuous demonstration mode showing live measurements.
        
        Args:
            duration: How long to run (seconds)
        """
        print(f"\n{'='*60}")
        print("DEMO MODE - Live Measurements")
        print(f"{'='*60}")
        print(f"Running for {duration:.0f} seconds...")
        print("Move sensor over various surfaces\n")
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while (time.time() - start_time) < duration:
                dist = self.lidar.get_distance()
                if dist is not None and dist > 0:
                    dist_cm = dist * 100
                    sample_count += 1
                    
                    # Simple visualization
                    bar_length = int(dist_cm / 2)
                    bar = '█' * min(bar_length, 50)
                    
                    print(f"\r{dist_cm:6.2f} cm  {bar:<50}", end='', flush=True)
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\nDemo stopped by user")
        
        print(f"\n\nTotal samples: {sample_count}")
        print(f"Average rate:  {sample_count/duration:.1f} Hz")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pothole Measurement Calibration Tool")
    parser.add_argument(
        '--mode',
        choices=['calibrate', 'test', 'demo'],
        default='demo',
        help='Operation mode'
    )
    parser.add_argument(
        '--port',
        default='/dev/ttyAMA4',
        help='LiDAR serial port'
    )
    parser.add_argument(
        '--depth',
        type=float,
        help='Expected pothole depth for test mode (cm)'
    )
    parser.add_argument(
        '--length',
        type=float,
        help='Expected pothole length for test mode (cm)'
    )
    parser.add_argument(
        '--speed',
        type=float,
        default=30.0,
        help='Vehicle speed (cm/s)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Pothole Measurement Calibration Tool")
    print("=" * 60)
    
    calibrator = MeasurementCalibrator(lidar_port=args.port)
    
    if args.mode == 'calibrate':
        calibrator.measure_baseline()
    
    elif args.mode == 'test':
        if args.depth is None or args.length is None:
            print("Error: --depth and --length required for test mode")
            print("Example: --depth 10 --length 20")
            sys.exit(1)
        
        calibrator.test_known_pothole(
            expected_depth=args.depth,
            expected_length=args.length,
            vehicle_speed=args.speed
        )
    
    elif args.mode == 'demo':
        calibrator.demo_mode()
    
    print("\n" + "=" * 60)
    print("Calibration tool finished")
    print("=" * 60)


if __name__ == "__main__":
    main()
