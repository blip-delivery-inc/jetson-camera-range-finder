#!/usr/bin/env python3
"""
Obstacle detection example for Jetson Edge SDK
Combines camera and range finder data for navigation assistance
"""

import time
import sys
import os
import cv2
import numpy as np
import math

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jetson_edge_sdk import JetsonEdgeSDK


class ObstacleDetector:
    """Detects obstacles using both camera and range finder"""
    
    def __init__(self):
        self.safe_distance = 2.0  # meters
        self.warning_distance = 1.0  # meters
        self.latest_frame = None
        self.latest_obstacles = {}
        
    def analyze_frame(self, frame):
        """Simple visual obstacle detection using edge detection"""
        self.latest_frame = frame.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area (potential obstacles)
        min_area = 1000
        obstacles = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                obstacles.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'center': (x + w//2, y + h//2)
                })
        
        return obstacles
    
    def analyze_range_data(self, scan_data):
        """Analyze range finder data for obstacles"""
        if not scan_data or not scan_data.readings:
            return {}
        
        obstacles = {}
        
        # Group readings by sectors
        sectors = {
            'front': (330, 30),      # -30° to +30°
            'front_left': (30, 90),  # 30° to 90°
            'left': (90, 150),       # 90° to 150°
            'back_left': (150, 210), # 150° to 210°
            'back': (210, 270),      # 210° to 270°
            'back_right': (270, 330), # 270° to 330°
            'right': (270, 330),     # 270° to 330°
            'front_right': (330, 360) # 330° to 360°
        }
        
        for sector_name, (start_angle, end_angle) in sectors.items():
            sector_readings = []
            
            for reading in scan_data.readings:
                angle = reading.angle
                
                # Handle wraparound for front sector
                if sector_name == 'front':
                    if angle >= start_angle or angle <= end_angle:
                        sector_readings.append(reading)
                else:
                    if start_angle <= angle <= end_angle:
                        sector_readings.append(reading)
            
            if sector_readings:
                # Find closest obstacle in this sector
                closest = min(sector_readings, key=lambda r: r.distance)
                
                # Classify threat level
                if closest.distance < self.warning_distance:
                    threat_level = 'DANGER'
                elif closest.distance < self.safe_distance:
                    threat_level = 'WARNING'
                else:
                    threat_level = 'SAFE'
                
                obstacles[sector_name] = {
                    'distance': closest.distance,
                    'angle': closest.angle,
                    'threat_level': threat_level,
                    'readings_count': len(sector_readings)
                }
        
        self.latest_obstacles = obstacles
        return obstacles
    
    def create_visualization(self, frame, visual_obstacles, range_obstacles):
        """Create visualization combining camera and range finder data"""
        vis_frame = frame.copy()
        height, width = vis_frame.shape[:2]
        
        # Draw visual obstacles (bounding boxes)
        for obs in visual_obstacles:
            x, y, w, h = obs['bbox']
            cv2.rectangle(vis_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(vis_frame, f"Area: {obs['area']}", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw range finder data overlay
        center_x, center_y = width // 2, height - 50
        max_range_pixels = 200
        
        # Draw range finder visualization
        for sector, data in range_obstacles.items():
            angle_rad = math.radians(data['angle'])
            distance_pixels = min(data['distance'] * 50, max_range_pixels)  # Scale distance
            
            end_x = int(center_x + distance_pixels * math.sin(angle_rad))
            end_y = int(center_y - distance_pixels * math.cos(angle_rad))
            
            # Color based on threat level
            color = {
                'DANGER': (0, 0, 255),    # Red
                'WARNING': (0, 165, 255), # Orange
                'SAFE': (0, 255, 0)       # Green
            }.get(data['threat_level'], (128, 128, 128))
            
            cv2.line(vis_frame, (center_x, center_y), (end_x, end_y), color, 3)
            
            # Draw distance text
            text_x = int(center_x + (distance_pixels + 20) * math.sin(angle_rad))
            text_y = int(center_y - (distance_pixels + 20) * math.cos(angle_rad))
            cv2.putText(vis_frame, f"{data['distance']:.1f}m", 
                       (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Draw status panel
        panel_height = 120
        panel = np.zeros((panel_height, width, 3), dtype=np.uint8)
        
        y_pos = 20
        for sector, data in range_obstacles.items():
            status_text = f"{sector}: {data['distance']:.1f}m ({data['threat_level']})"
            color = {
                'DANGER': (0, 0, 255),
                'WARNING': (0, 165, 255),
                'SAFE': (0, 255, 0)
            }.get(data['threat_level'], (255, 255, 255))
            
            cv2.putText(panel, status_text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            y_pos += 15
        
        # Combine frame and panel
        vis_frame = np.vstack([vis_frame, panel])
        
        return vis_frame


def main():
    """Obstacle detection example"""
    print("Jetson Edge SDK - Obstacle Detection Example")
    print("===========================================")
    
    # Initialize detector
    detector = ObstacleDetector()
    
    # Initialize SDK
    sdk = JetsonEdgeSDK()
    
    try:
        # Initialize hardware
        print("Initializing hardware...")
        if not sdk.initialize(use_csi_camera=False):  # Set to True for CSI camera
            print("Failed to initialize SDK")
            return
        
        # Start operations
        print("Starting obstacle detection...")
        if not sdk.start():
            print("Failed to start operations")
            return
        
        # Wait for data
        print("Waiting for sensor data...")
        if not sdk.wait_for_data(timeout=10.0):
            print("Timeout waiting for data")
            return
        
        print("Obstacle detection running! Press 'q' to quit, 's' to save frame.")
        print()
        
        frame_count = 0
        last_save_time = 0
        
        while True:
            try:
                # Get latest data
                frame = sdk.get_camera_frame()
                scan = sdk.get_range_scan()
                
                if frame is not None and scan is not None:
                    frame_count += 1
                    
                    # Analyze visual obstacles
                    visual_obstacles = detector.analyze_frame(frame)
                    
                    # Analyze range data
                    range_obstacles = detector.analyze_range_data(scan)
                    
                    # Create visualization
                    vis_frame = detector.create_visualization(frame, visual_obstacles, range_obstacles)
                    
                    # Display results
                    cv2.imshow('Obstacle Detection', vis_frame)
                    
                    # Print status every 30 frames
                    if frame_count % 30 == 0:
                        print(f"\nFrame {frame_count}:")
                        print(f"Visual obstacles detected: {len(visual_obstacles)}")
                        
                        # Check for immediate dangers
                        dangers = [s for s, d in range_obstacles.items() 
                                 if d['threat_level'] == 'DANGER']
                        warnings = [s for s, d in range_obstacles.items() 
                                  if d['threat_level'] == 'WARNING']
                        
                        if dangers:
                            print(f"🚨 DANGER: Obstacles in {', '.join(dangers)}")
                        elif warnings:
                            print(f"⚠️  WARNING: Obstacles in {', '.join(warnings)}")
                        else:
                            print("✅ Path appears clear")
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting...")
                    break
                elif key == ord('s'):
                    # Save current visualization
                    current_time = time.time()
                    if current_time - last_save_time > 1.0:  # Prevent spam saving
                        timestamp = int(current_time)
                        filename = f"./data/obstacle_detection_{timestamp}.jpg"
                        if frame is not None:
                            vis_frame = detector.create_visualization(
                                frame, 
                                detector.analyze_frame(frame),
                                detector.latest_obstacles
                            )
                            cv2.imwrite(filename, vis_frame)
                            print(f"Saved visualization to {filename}")
                            last_save_time = current_time
                
                time.sleep(0.03)  # ~30 FPS
                
            except KeyboardInterrupt:
                print("\nStopping...")
                break
        
        # Cleanup
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean shutdown
        print("Shutting down...")
        sdk.stop()
        sdk.release()
        cv2.destroyAllWindows()
        print("Done!")


if __name__ == "__main__":
    main()