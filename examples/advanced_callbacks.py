#!/usr/bin/env python3
"""
Advanced callback example for Jetson Edge SDK
Demonstrates real-time processing using callbacks
"""

import time
import sys
import os
import cv2
import numpy as np

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jetson_edge_sdk import JetsonEdgeSDK


class DataProcessor:
    """Processes camera and range finder data in real-time"""
    
    def __init__(self):
        self.frame_count = 0
        self.scan_count = 0
        self.obstacle_detected = False
        self.min_safe_distance = 1.0  # meters
        
    def frame_callback(self, frame):
        """Process each camera frame"""
        self.frame_count += 1
        
        # Example processing: detect edges
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Count edge pixels as a simple activity measure
        edge_pixels = np.sum(edges > 0)
        
        if self.frame_count % 30 == 0:  # Print every 30 frames
            print(f"Frame {self.frame_count}: Edge pixels = {edge_pixels}")
            
            # Save processed frame occasionally
            if self.frame_count % 150 == 0:  # Every 150 frames
                filename = f"./data/edges_frame_{self.frame_count}.jpg"
                cv2.imwrite(filename, edges)
                print(f"  Saved edge detection to {filename}")
    
    def scan_callback(self, scan_data):
        """Process each range finder scan"""
        self.scan_count += 1
        
        if not scan_data.readings:
            return
        
        # Check for obstacles in front (±30 degrees from front)
        front_readings = [
            r for r in scan_data.readings 
            if (r.angle <= 30 or r.angle >= 330) and r.distance < self.min_safe_distance
        ]
        
        # Check for obstacles on sides
        left_readings = [
            r for r in scan_data.readings 
            if 60 <= r.angle <= 120 and r.distance < self.min_safe_distance
        ]
        
        right_readings = [
            r for r in scan_data.readings 
            if 240 <= r.angle <= 300 and r.distance < self.min_safe_distance
        ]
        
        # Update obstacle status
        self.obstacle_detected = len(front_readings) > 0
        
        if self.scan_count % 10 == 0:  # Print every 10 scans
            print(f"Scan {self.scan_count}: {len(scan_data.readings)} readings")
            print(f"  Obstacles - Front: {len(front_readings)}, Left: {len(left_readings)}, Right: {len(right_readings)}")
            
            if self.obstacle_detected:
                print("  ⚠️  OBSTACLE DETECTED IN FRONT!")
            
            # Find closest obstacle
            closest_reading = min(scan_data.readings, key=lambda r: r.distance)
            print(f"  Closest obstacle: {closest_reading.distance:.2f}m at {closest_reading.angle:.1f}°")


def main():
    """Advanced callback example"""
    print("Jetson Edge SDK - Advanced Callbacks Example")
    print("===========================================")
    
    # Create data processor
    processor = DataProcessor()
    
    # Initialize SDK with custom configuration
    config_path = "config.json"
    sdk = JetsonEdgeSDK(config_path)
    
    try:
        # Initialize hardware
        print("Initializing hardware...")
        if not sdk.initialize(use_csi_camera=False):  # Set to True for CSI camera
            print("Failed to initialize SDK")
            return
        
        # Start operations with callbacks
        print("Starting operations with callbacks...")
        if not sdk.start(
            frame_callback=processor.frame_callback,
            scan_callback=processor.scan_callback
        ):
            print("Failed to start operations")
            return
        
        print("SDK is running with real-time processing!")
        print("Press Ctrl+C to stop.")
        print()
        
        # Monitor for 60 seconds or until interrupted
        start_time = time.time()
        last_status_time = 0
        
        try:
            while time.time() - start_time < 60.0:
                current_time = time.time()
                
                # Print status every 5 seconds
                if current_time - last_status_time >= 5.0:
                    print(f"\n--- Status Update (Running for {int(current_time - start_time)}s) ---")
                    print(f"Frames processed: {processor.frame_count}")
                    print(f"Scans processed: {processor.scan_count}")
                    print(f"Obstacle detected: {'YES' if processor.obstacle_detected else 'NO'}")
                    
                    # Get system status
                    status = sdk.get_system_status()
                    print(f"Camera status: {status['camera']['status']}")
                    print(f"Range finder connected: {status['range_finder']['is_connected']}")
                    print()
                    
                    last_status_time = current_time
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nStopping...")
        
        # Final statistics
        total_time = time.time() - start_time
        print(f"\n=== Final Statistics ===")
        print(f"Total runtime: {total_time:.1f} seconds")
        print(f"Total frames processed: {processor.frame_count}")
        print(f"Total scans processed: {processor.scan_count}")
        print(f"Average frame rate: {processor.frame_count / total_time:.1f} FPS")
        print(f"Average scan rate: {processor.scan_count / total_time:.1f} scans/sec")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean shutdown
        print("Shutting down...")
        sdk.stop()
        sdk.release()
        print("Done!")


if __name__ == "__main__":
    main()