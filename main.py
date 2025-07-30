import time
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from camera import CameraManager, SimpleCamera
from lidar import LIDARManager, SimpleLIDAR, LIDARData
    import cv2
#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Main Application

This script demonstrates the integration of camera and LIDAR data acquisition
on the Jetson Orin platform. It provides a simple interface for capturing
images and retrieving range data simultaneously.

Author: Jetson Orin SDK
"""



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jetson_sdk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JetsonOrinSDK:
    """Main SDK class that integrates camera and LIDAR functionality."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Jetson Orin SDK.
        
        Args:
            output_dir: Directory to save captured data
        """
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            self.output_dir.mkdir(exist_ok=True)
        
        # Initialize managers
        self.camera_manager = CameraManager()
        self.lidar_manager = LIDARManager()
        
        # Connected devices
        self.connected_cameras = {}
        self.connected_lidars = {}
        
        # Data storage
        self.camera_data = []
        self.lidar_data = []
        
        logger.info("Jetson Orin SDK initialized")
    
    def detect_hardware(self) -> Dict[str, Any]:
        """
        Detect all available camera and LIDAR hardware.
        
        Returns:
            Dictionary containing detected hardware information
        """
        logger.info("Detecting hardware...")
        
        # Detect cameras
        cameras = self.camera_manager.detect_cameras()
        logger.info(f"Detected {len(cameras)} cameras")
        
        # Detect LIDARs
        lidars = self.lidar_manager.detect_lidars()
        logger.info(f"Detected {len(lidars)} LIDAR devices")
        
        hardware_info = {
            'timestamp': datetime.now().isoformat(),
            'cameras': cameras,
            'lidars': lidars,
            'total_devices': len(cameras) + len(lidars)
        }
        
        # Save hardware detection results
        try:
            with open(self.output_dir / 'hardware_detection.json', 'w') as f:
            try:
                json.dump(hardware_info, f, indent=2)
            except IOError as e:
                print(f"Error writing JSON: {e}")
        
        logger.info(f"Hardware detection complete: {hardware_info['total_devices']} devices found")
        return hardware_info
    
    def connect_hardware(self, hardware_info: Dict[str, Any]) -> bool:
        """
        Connect to detected hardware.
        
        Args:
            hardware_info: Hardware detection results
            
        Returns:
            True if at least one device connected successfully
        """
        logger.info("Connecting to hardware...")
        
        success = False
        
        # Connect to cameras
        for camera_info in hardware_info['cameras']:
            if self.camera_manager.connect_camera(camera_info['id'], camera_info):
                self.connected_cameras[camera_info['id']] = camera_info
                success = True
                logger.info(f"Connected to camera: {camera_info['id']}")
        
        # Connect to LIDARs
        for lidar_info in hardware_info['lidars']:
            if self.lidar_manager.connect_lidar(lidar_info['id'], lidar_info):
                self.connected_lidars[lidar_info['id']] = lidar_info
                success = True
                logger.info(f"Connected to LIDAR: {lidar_info['id']}")
        
        if not success:
            logger.warning("No hardware devices connected successfully")
        else:
            logger.info(f"Hardware connection complete: {len(self.connected_cameras)} cameras, {len(self.connected_lidars)} LIDARs")
        
        return success
    
    def capture_data(self, duration: float = 5.0, interval: float = 1.0) -> Dict[str, Any]:
        """
        Capture data from all connected devices for a specified duration.
        
        Args:
            duration: Total capture duration in seconds
            interval: Time interval between captures in seconds
            
        Returns:
            Dictionary containing captured data summary
        """
        logger.info(f"Starting data capture for {duration} seconds (interval: {interval}s)")
        
        start_time = time.time()
        capture_count = 0
        
        while time.time() - start_time < duration:
            capture_time = datetime.now()
            capture_data = {
                'timestamp': capture_time.isoformat(),
                'cameras': {},
                'lidars': {}
            }
            
            # Capture from cameras
            for camera_id in self.connected_cameras:
                frame = self.camera_manager.capture_frame(camera_id)
                if frame is not None:
                    # Save frame
                    frame_filename = f"camera_{camera_id}_{capture_time.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                    frame_path = self.output_dir / frame_filename
                    
                    try:
except ImportError:
    cv2 = None
    print("Warning: OpenCV not available. Camera functionality will be limited.")
                    if cv2.imwrite(str(frame_path), frame):
                        capture_data['cameras'][camera_id] = {
                            'frame_path': str(frame_path),
                            'frame_shape': frame.shape,
                            'status': 'success'
                        }
                        self.camera_data.append(capture_data['cameras'][camera_id])
                    else:
                        capture_data['cameras'][camera_id] = {
                            'status': 'failed',
                            'error': 'Failed to save frame'
                        }
            else:
                capture_data['cameras'][camera_id] = {
                    'status': 'failed',
                    'error': 'Failed to capture frame'
                }
            
            # Capture from LIDARs
            for lidar_id in self.connected_lidars:
                lidar_data = self.lidar_manager.read_data(lidar_id)
                if lidar_data is not None:
                    capture_data['lidars'][lidar_id] = {
                        'distance': lidar_data.distance,
                        'angle': lidar_data.angle,
                        'quality': lidar_data.quality,
                        'status': 'success'
                    }
                    self.lidar_data.append(capture_data['lidars'][lidar_id])
                    logger.info(f"LIDAR {lidar_id}: {lidar_data}")
                else:
                    capture_data['lidars'][lidar_id] = {
                        'status': 'failed',
                        'error': 'Failed to read data'
                    }
            
            capture_count += 1
            logger.info(f"Capture {capture_count}: {len(capture_data['cameras'])} camera frames, {len(capture_data['lidars'])} LIDAR readings")
            
            # Wait for next interval
            time.sleep(interval)
        
        # Save capture summary
        summary = {
            'capture_duration': duration,
            'capture_interval': interval,
            'total_captures': capture_count,
            'camera_captures': len(self.camera_data),
            'lidar_captures': len(self.lidar_data),
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        try:
            with open(self.output_dir / 'capture_summary.json', 'w') as f:
            try:
                json.dump(summary, f, indent=2)
            except IOError as e:
                print(f"Error writing JSON: {e}")
        
        logger.info(f"Data capture complete: {summary}")
        return summary
    
    def simple_capture(self) -> Dict[str, Any]:
        """
        Perform a simple single capture from available devices.
        
        Returns:
            Dictionary containing captured data
        """
        logger.info("Performing simple capture...")
        
        capture_data = {
            'timestamp': datetime.now().isoformat(),
            'cameras': {},
            'lidars': {}
        }
        
        # Simple camera capture
        camera = SimpleCamera()
        if camera.connect():
            frame = camera.capture()
            if frame is not None:
                frame_filename = f"simple_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                frame_path = self.output_dir / frame_filename
                try:
except ImportError:
    cv2 = None
    print("Warning: OpenCV not available. Camera functionality will be limited.")
                cv2.imwrite(str(frame_path), frame)
                
                capture_data['cameras']['simple'] = {
                    'frame_path': str(frame_path),
                    'frame_shape': frame.shape,
                    'status': 'success'
                }
                logger.info(f"Simple camera capture: {frame.shape}")
            camera.disconnect()
        
        # Simple LIDAR capture
        lidar = SimpleLIDAR()
        if lidar.connect():
            distance = lidar.read_distance()
            if distance is not None:
                capture_data['lidars']['simple'] = {
                    'distance': distance,
                    'angle': 0.0,
                    'status': 'success'
                }
                logger.info(f"Simple LIDAR capture: {distance:.3f}m")
            lidar.disconnect()
        
        return capture_data
    
    def cleanup(self):
        """Clean up all connections and resources."""
        logger.info("Cleaning up resources...")
        
        self.camera_manager.disconnect_all()
        self.lidar_manager.disconnect_all()
        
        self.connected_cameras.clear()
        self.connected_lidars.clear()
        
        logger.info("Cleanup complete")


def main():
    """Main application entry point."""
    logger.info("=== Jetson Orin Integration SDK ===")
    logger.info("Starting hardware detection and data capture...")
    
    try:
        # Initialize SDK
        sdk = JetsonOrinSDK()
        
        # Detect hardware
        hardware_info = sdk.detect_hardware()
        
        # Connect to hardware
        if sdk.connect_hardware(hardware_info):
            # Perform simple capture first
            simple_data = sdk.simple_capture()
            logger.info("Simple capture completed")
            
            # Perform extended capture if devices are available
            if len(sdk.connected_cameras) > 0 or len(sdk.connected_lidars) > 0:
                logger.info("Starting extended capture...")
                capture_summary = sdk.capture_data(duration=10.0, interval=2.0)
                logger.info("Extended capture completed")
            else:
                logger.info("No devices connected, skipping extended capture")
        else:
            logger.warning("No hardware connected, performing simple capture only")
            simple_data = sdk.simple_capture()
        
        logger.info("=== SDK Test Complete ===")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except IOError as e:
        logger.error(f"Application error: {str(e)}")
    finally:
        if 'sdk' in locals():
            sdk.cleanup()


if __name__ == "__main__":
    main()