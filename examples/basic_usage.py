#!/usr/bin/env python3
"""
Basic usage example for Jetson Edge SDK
Demonstrates the simplest way to capture camera frames and range finder data
"""

import time
import sys
import os

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jetson_edge_sdk import JetsonEdgeSDK


def main():
    """Basic usage example"""
    print("Jetson Edge SDK - Basic Usage Example")
    print("=====================================")
    
    # Initialize SDK with default configuration
    sdk = JetsonEdgeSDK()
    
    try:
        # Initialize hardware (use USB camera for this example)
        print("Initializing hardware...")
        if not sdk.initialize(use_csi_camera=False):  # Set to True for CSI camera
            print("Failed to initialize SDK")
            return
        
        # Start operations
        print("Starting operations...")
        if not sdk.start():
            print("Failed to start operations")
            return
        
        # Wait for data to be available
        print("Waiting for data...")
        if not sdk.wait_for_data(timeout=10.0):
            print("Timeout waiting for data")
            return
        
        print("SDK is running! Press Ctrl+C to stop.")
        print()
        
        # Main loop - capture data for 30 seconds
        start_time = time.time()
        frame_count = 0
        scan_count = 0
        
        while time.time() - start_time < 30.0:
            try:
                # Get camera frame
                frame = sdk.get_camera_frame()
                if frame is not None:
                    frame_count += 1
                    if frame_count % 30 == 0:  # Print every 30 frames
                        print(f"Captured {frame_count} frames, frame shape: {frame.shape}")
                
                # Get range finder scan
                scan = sdk.get_range_scan()
                if scan is not None:
                    scan_count += 1
                    if scan_count % 10 == 0:  # Print every 10 scans
                        print(f"Received {scan_count} scans, readings: {len(scan.readings)}")
                        
                        # Show some distance measurements at key angles
                        front_dist = sdk.get_distance_at_angle(0)  # Front
                        left_dist = sdk.get_distance_at_angle(90)   # Left
                        right_dist = sdk.get_distance_at_angle(270) # Right
                        
                        print(f"  Distances - Front: {front_dist:.2f}m, Left: {left_dist:.2f}m, Right: {right_dist:.2f}m"
                              if all(d is not None for d in [front_dist, left_dist, right_dist])
                              else "  Distance data not available")
                
                # Save a frame every 5 seconds
                if int(time.time() - start_time) % 5 == 0 and frame is not None:
                    timestamp = int(time.time())
                    if sdk.save_camera_frame(f"./data/example_frame_{timestamp}.jpg"):
                        print(f"Saved frame to ./data/example_frame_{timestamp}.jpg")
                
                time.sleep(0.1)  # Small delay
                
            except KeyboardInterrupt:
                print("\nStopping...")
                break
        
        # Print final statistics
        print(f"\nFinal statistics:")
        print(f"Total frames captured: {frame_count}")
        print(f"Total scans received: {scan_count}")
        
        # Get system status
        status = sdk.get_system_status()
        print(f"\nSystem Status:")
        print(f"Camera: {status['camera']['status']}")
        print(f"Range Finder: {status['range_finder']['is_connected']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean shutdown
        print("Shutting down...")
        sdk.stop()
        sdk.release()
        print("Done!")


if __name__ == "__main__":
    main()