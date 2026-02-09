#!/usr/bin/env python3
"""
Advanced Pothole Measurement System using TF02-Pro LiDAR

This module provides accurate measurement of pothole dimensions:
- Depth: Maximum deviation from road surface
- Length: Distance traveled during pothole event
- Width: Estimated using cross-sectional analysis

Author: Pothole Detection System
Date: 2026-02-10
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging


@dataclass
class PotholeMeasurement:
    """Data class for pothole measurements."""
    max_depth: float  # cm
    avg_depth: float  # cm
    length: float  # cm
    width: float  # cm
    volume: float  # cm³
    confidence: float  # 0-1
    sample_count: int
    duration: float  # seconds
    depth_profile: List[float]  # All depth readings


class PotholeAnalyzer:
    """
    Advanced pothole measurement analyzer using LiDAR data.
    
    This class processes LiDAR readings to accurately measure pothole dimensions
    using statistical analysis and geometric modeling.
    """
    
    def __init__(
        self,
        vehicle_speed: float = 30.0,  # cm/s
        sensor_height: float = 15.0,  # cm above road surface
        sampling_rate: float = 20.0,  # Hz
        road_surface_threshold: float = 2.0,  # cm tolerance for road surface
    ):
        """
        Initialize the pothole analyzer.
        
        Args:
            vehicle_speed: Speed of vehicle/robot in cm/s
            sensor_height: Height of LiDAR sensor above normal road surface (cm)
            sampling_rate: LiDAR sampling frequency (Hz)
            road_surface_threshold: Tolerance for road surface detection (cm)
        """
        self.vehicle_speed = vehicle_speed
        self.sensor_height = sensor_height
        self.sampling_rate = sampling_rate
        self.road_surface_threshold = road_surface_threshold
        self.logger = logging.getLogger('PotholeAnalyzer')
        
    def analyze_pothole(
        self,
        depth_readings: List[float],
        duration: float,
        baseline_distance: Optional[float] = None
    ) -> PotholeMeasurement:
        """
        Analyze pothole dimensions from LiDAR readings.
        
        Args:
            depth_readings: List of LiDAR distance readings (cm)
            duration: Duration of the pothole event (seconds)
            baseline_distance: Known road surface distance (cm). If None, estimated.
            
        Returns:
            PotholeMeasurement object with all dimensions
        """
        if not depth_readings or len(depth_readings) < 3:
            raise ValueError("Insufficient readings for analysis (minimum 3 required)")
        
        # Convert to numpy array for easier processing
        readings = np.array(depth_readings)
        
        # Step 1: Establish baseline (road surface level)
        if baseline_distance is None:
            baseline_distance = self._estimate_baseline(readings)
        
        # Step 2: Calculate depth measurements
        # Depth = how much deeper than road surface
        # Positive values = pothole (deeper than surface)
        depth_deviations = readings - baseline_distance
        
        # Filter out negative deviations (bumps, not potholes)
        pothole_depths = depth_deviations[depth_deviations > 0]
        
        if len(pothole_depths) == 0:
            # No actual pothole detected
            return PotholeMeasurement(
                max_depth=0,
                avg_depth=0,
                length=0,
                width=0,
                volume=0,
                confidence=0.0,
                sample_count=len(readings),
                duration=duration,
                depth_profile=depth_readings
            )
        
        # Step 3: Calculate depth statistics
        max_depth = float(np.max(pothole_depths))
        avg_depth = float(np.mean(pothole_depths))
        
        # Step 4: Calculate length
        # Length = distance traveled during pothole event
        length = self._calculate_length(duration, len(pothole_depths), len(readings))
        
        # Step 5: Calculate width using cross-sectional analysis
        width = self._calculate_width(pothole_depths, max_depth, length)
        
        # Step 6: Calculate volume (approximation)
        volume = self._calculate_volume(pothole_depths, length, width)
        
        # Step 7: Calculate confidence score
        confidence = self._calculate_confidence(
            readings, pothole_depths, baseline_distance
        )
        
        return PotholeMeasurement(
            max_depth=round(max_depth, 2),
            avg_depth=round(avg_depth, 2),
            length=round(length, 2),
            width=round(width, 2),
            volume=round(volume, 2),
            confidence=round(confidence, 2),
            sample_count=len(readings),
            duration=duration,
            depth_profile=depth_readings
        )
    
    def _estimate_baseline(self, readings: np.ndarray) -> float:
        """
        Estimate the road surface baseline from readings.
        
        Uses the minimum readings (closest to sensor) as baseline,
        assuming the road surface is the most common distance.
        
        Args:
            readings: Array of LiDAR readings
            
        Returns:
            Estimated baseline distance (cm)
        """
        # Method 1: Use minimum value (most conservative)
        # This assumes the shallowest reading is the road surface
        min_reading = np.min(readings)
        
        # Method 2: Use mode (most common value) for robustness
        # Bin the readings and find the most common bin
        hist, bin_edges = np.histogram(readings, bins=20)
        most_common_bin = np.argmax(hist)
        mode_estimate = (bin_edges[most_common_bin] + bin_edges[most_common_bin + 1]) / 2
        
        # Method 3: Use first few readings (before pothole)
        # Assume first 20% of readings are road surface
        pre_pothole_count = max(3, int(len(readings) * 0.2))
        pre_pothole_avg = np.mean(readings[:pre_pothole_count])
        
        # Use the minimum of these methods for safety
        baseline = min(min_reading, mode_estimate, pre_pothole_avg)
        
        self.logger.debug(
            f"Baseline estimation: min={min_reading:.2f}, "
            f"mode={mode_estimate:.2f}, pre_avg={pre_pothole_avg:.2f}, "
            f"selected={baseline:.2f}"
        )
        
        return float(baseline)
    
    def _calculate_length(
        self,
        duration: float,
        pothole_samples: int,
        total_samples: int
    ) -> float:
        """
        Calculate pothole length based on travel distance.
        
        Args:
            duration: Total event duration (seconds)
            pothole_samples: Number of samples within pothole
            total_samples: Total number of samples
            
        Returns:
            Estimated length (cm)
        """
        # Method 1: Total distance traveled during event
        total_distance = duration * self.vehicle_speed
        
        # Method 2: Proportional to pothole samples
        # More accurate if vehicle speed varies
        pothole_ratio = pothole_samples / total_samples if total_samples > 0 else 1.0
        proportional_length = total_distance * pothole_ratio
        
        # Use the proportional method as it's more accurate
        length = proportional_length
        
        # Sanity check: length should be reasonable (5cm to 200cm)
        length = max(5.0, min(length, 200.0))
        
        self.logger.debug(
            f"Length calculation: duration={duration:.2f}s, "
            f"speed={self.vehicle_speed:.2f}cm/s, "
            f"ratio={pothole_ratio:.2f}, length={length:.2f}cm"
        )
        
        return length
    
    def _calculate_width(
        self,
        pothole_depths: np.ndarray,
        max_depth: float,
        length: float
    ) -> float:
        """
        Calculate pothole width using cross-sectional analysis.
        
        For a point LiDAR, we estimate width based on:
        1. Depth profile shape
        2. Length-to-width ratio (typical potholes are 0.6-1.2 ratio)
        3. Depth-to-width correlation
        
        Args:
            pothole_depths: Array of depth measurements
            max_depth: Maximum depth
            length: Calculated length
            
        Returns:
            Estimated width (cm)
        """
        # Method 1: Geometric model based on depth
        # Wider potholes tend to be deeper
        # Empirical formula: width ≈ 2.5 * sqrt(depth)
        depth_based_width = 2.5 * np.sqrt(max_depth)
        
        # Method 2: Length-based estimation
        # Typical potholes have length:width ratio of 0.8-1.2
        # Use 0.85 as conservative estimate
        length_based_width = length * 0.85
        
        # Method 3: Profile-based estimation
        # Analyze the depth profile shape
        # Wider potholes have more gradual depth changes
        if len(pothole_depths) > 5:
            depth_variance = np.std(pothole_depths)
            variance_based_width = depth_variance * 3.0
        else:
            variance_based_width = length_based_width
        
        # Weighted average of methods
        # Prioritize length-based for consistency
        width = (
            length_based_width * 0.5 +
            depth_based_width * 0.3 +
            variance_based_width * 0.2
        )
        
        # Sanity check: width should be reasonable (5cm to 150cm)
        width = max(5.0, min(width, 150.0))
        
        # Width should not be more than 1.5x length (unrealistic)
        width = min(width, length * 1.5)
        
        self.logger.debug(
            f"Width calculation: depth_based={depth_based_width:.2f}, "
            f"length_based={length_based_width:.2f}, "
            f"variance_based={variance_based_width:.2f}, "
            f"final={width:.2f}cm"
        )
        
        return width
    
    def _calculate_volume(
        self,
        pothole_depths: np.ndarray,
        length: float,
        width: float
    ) -> float:
        """
        Calculate approximate pothole volume.
        
        Uses elliptical bowl approximation:
        V = (π/6) × length × width × avg_depth
        
        Args:
            pothole_depths: Array of depth measurements
            length: Pothole length (cm)
            width: Pothole width (cm)
            
        Returns:
            Estimated volume (cm³)
        """
        avg_depth = float(np.mean(pothole_depths))
        
        # Elliptical bowl model
        volume = (np.pi / 6) * length * width * avg_depth
        
        self.logger.debug(
            f"Volume calculation: L={length:.2f}, W={width:.2f}, "
            f"D_avg={avg_depth:.2f}, V={volume:.2f}cm³"
        )
        
        return volume
    
    def _calculate_confidence(
        self,
        all_readings: np.ndarray,
        pothole_depths: np.ndarray,
        baseline: float
    ) -> float:
        """
        Calculate confidence score for the measurement.
        
        Factors:
        - Sample count (more samples = higher confidence)
        - Depth consistency (less variance = higher confidence)
        - Clear pothole signature (distinct from baseline)
        
        Args:
            all_readings: All LiDAR readings
            pothole_depths: Filtered pothole depth readings
            baseline: Estimated baseline distance
            
        Returns:
            Confidence score (0-1)
        """
        confidence_factors = []
        
        # Factor 1: Sample count (min 5 for good confidence)
        sample_confidence = min(len(pothole_depths) / 10.0, 1.0)
        confidence_factors.append(sample_confidence)
        
        # Factor 2: Depth consistency
        if len(pothole_depths) > 1:
            depth_std = np.std(pothole_depths)
            depth_mean = np.mean(pothole_depths)
            cv = depth_std / depth_mean if depth_mean > 0 else 1.0
            # Lower coefficient of variation = higher confidence
            consistency_confidence = max(0, 1.0 - cv)
            confidence_factors.append(consistency_confidence)
        
        # Factor 3: Clear distinction from baseline
        max_depth = np.max(pothole_depths)
        distinction_ratio = max_depth / self.road_surface_threshold
        distinction_confidence = min(distinction_ratio / 3.0, 1.0)
        confidence_factors.append(distinction_confidence)
        
        # Factor 4: Profile shape (should have rise and fall)
        if len(all_readings) > 5:
            # Check if readings increase then decrease (pothole signature)
            first_half = all_readings[:len(all_readings)//2]
            second_half = all_readings[len(all_readings)//2:]
            
            first_trend = np.mean(np.diff(first_half))
            second_trend = np.mean(np.diff(second_half))
            
            # Good pothole: first half increases, second half decreases
            if first_trend > 0 and second_trend < 0:
                shape_confidence = 1.0
            else:
                shape_confidence = 0.5
            
            confidence_factors.append(shape_confidence)
        
        # Overall confidence is the average of all factors
        overall_confidence = np.mean(confidence_factors)
        
        self.logger.debug(
            f"Confidence factors: sample={sample_confidence:.2f}, "
            f"consistency={confidence_factors[1] if len(confidence_factors) > 1 else 0:.2f}, "
            f"distinction={distinction_confidence:.2f}, "
            f"overall={overall_confidence:.2f}"
        )
        
        return float(overall_confidence)


# Convenience function for quick analysis
def measure_pothole(
    depth_readings: List[float],
    duration: float,
    vehicle_speed: float = 30.0,
    sensor_height: float = 15.0
) -> Dict[str, float]:
    """
    Quick pothole measurement function.
    
    Args:
        depth_readings: List of LiDAR distance readings (cm)
        duration: Duration of pothole event (seconds)
        vehicle_speed: Vehicle speed (cm/s)
        sensor_height: Sensor height above road (cm)
        
    Returns:
        Dictionary with measurement results
    """
    analyzer = PotholeAnalyzer(
        vehicle_speed=vehicle_speed,
        sensor_height=sensor_height
    )
    
    result = analyzer.analyze_pothole(depth_readings, duration)
    
    return {
        'max_depth': result.max_depth,
        'avg_depth': result.avg_depth,
        'length': result.length,
        'width': result.width,
        'volume': result.volume,
        'confidence': result.confidence,
        'sample_count': result.sample_count
    }


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("Pothole Measurement System - Test")
    print("=" * 60)
    
    # Simulate a pothole event
    # Normal road surface at 15cm, pothole goes to 25cm (10cm deep)
    test_readings = [
        15.0, 15.1, 15.0,  # Approaching pothole
        16.0, 18.0, 22.0, 25.0, 24.0, 22.0, 18.0, 16.0,  # In pothole
        15.0, 15.1, 15.0   # Exiting pothole
    ]
    
    test_duration = len(test_readings) / 20.0  # 20Hz sampling
    
    analyzer = PotholeAnalyzer(vehicle_speed=30.0)
    result = analyzer.analyze_pothole(test_readings, test_duration)
    
    print(f"\nTest Pothole Measurements:")
    print(f"  Max Depth:    {result.max_depth:.2f} cm")
    print(f"  Avg Depth:    {result.avg_depth:.2f} cm")
    print(f"  Length:       {result.length:.2f} cm")
    print(f"  Width:        {result.width:.2f} cm")
    print(f"  Volume:       {result.volume:.2f} cm³")
    print(f"  Confidence:   {result.confidence:.2f} (0-1)")
    print(f"  Samples:      {result.sample_count}")
    print(f"  Duration:     {result.duration:.2f} s")
    print("=" * 60)
