#!/usr/bin/env python3
"""
Jetson Orin Camera Integration Module

This module provides easy-to-use interfaces for capturing images from
connected cameras (USB, CSI, IP) on the Jetson Orin platform.

Author: Jetson Orin SDK
"""

try:
    import cv2
except ImportError:
    cv2 = None
    print("Warning: OpenCV not available. Camera functionality will be limited.")
try:
    import numpy
except ImportError:
    numpy = None
    print("Warning: NumPy not available. Some functionality may be limited.") as np
import time
import logging
from typing import Optional, Tuple, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera connections and provides unified interface for different camera types."""
    
    def __init__(self):
        self.cameras = {}
        self.camera_configs = {
            'usb': {
                'default_device': 0,
                'width': 640,
                'height': 480,
                'fps': 30
            },
            'csi': {
                'default_device': 0,
                'width': 1920,
                'height': 1080,
                'fps': 30
            },
            'ip': {
                'default_url': 'http://192.168.1.100:8080/video',
                'timeout': 10
            }
        }
    
    def detect_cameras(self) -> List[dict]:
        """
        Detect available cameras on the system.
        
        Returns:
            List of detected camera information
        """
        detected_cameras = []
        
        # Check USB cameras (first 10 indices)
        for i in range(10):
            try:
            cap = cv2.VideoCapture(i)
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    detected_cameras.append({
                        'id': f'usb_{i}',
                        'type': 'usb',
                        'device_id': i,
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'description': f'USB Camera {i}'
                    })
                    logger.info(f"Detected USB camera {i}: {width}x{height} @ {fps}fps")
                cap.release()
        
        # Check CSI cameras (Jetson specific)
        csi_devices = ['/dev/video0', '/dev/video1', '/dev/video2']
        for device in csi_devices:
            if Path(device).exists():
                try:
            cap = cv2.VideoCapture(device)
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        detected_cameras.append({
                            'id': f'csi_{device}',
                            'type': 'csi',
                            'device_path': device,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'description': f'CSI Camera {device}'
                        })
                        logger.info(f"Detected CSI camera {device}: {width}x{height} @ {fps}fps")
                    cap.release()
        
        return detected_cameras
    
    def connect_camera(self, camera_id: str, camera_info: dict) -> bool:
        """
        Connect to a specific camera.
        
        Args:
            camera_id: Unique identifier for the camera
            camera_info: Camera configuration information
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if camera_info['type'] == 'usb':
                try:
            cap = cv2.VideoCapture(camera_info['device_id'])
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_info.get('width', 640))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_info.get('height', 480))
                cap.set(cv2.CAP_PROP_FPS, camera_info.get('fps', 30))
                
            elif camera_info['type'] == 'csi':
                try:
            cap = cv2.VideoCapture(camera_info['device_path'])
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_info.get('width', 1920))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_info.get('height', 1080))
                cap.set(cv2.CAP_PROP_FPS, camera_info.get('fps', 30))
                
            elif camera_info['type'] == 'ip':
                try:
            cap = cv2.VideoCapture(camera_info['url'])
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
            else:
                logger.error(f"Unsupported camera type: {camera_info['type']}")
                return False
            
            if cap.isOpened():
                self.cameras[camera_id] = {
                    'capture': cap,
                    'info': camera_info
                }
                logger.info(f"Successfully connected to camera: {camera_id}")
                return True
            else:
                logger.error(f"Failed to open camera: {camera_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to camera {camera_id}: {str(e)}")
            return False
    
    def capture_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """
        Capture a single frame from the specified camera.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Captured frame as numpy array, or None if failed
        """
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not connected")
            return None
        
        try:
            cap = self.cameras[camera_id]['capture']
            ret, frame = cap.read()
            
            if ret:
                return frame
            else:
                logger.warning(f"Failed to capture frame from camera {camera_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing frame from camera {camera_id}: {str(e)}")
            return None
    
    def save_frame(self, camera_id: str, filepath: str) -> bool:
        """
        Capture and save a frame to file.
        
        Args:
            camera_id: Camera identifier
            filepath: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        frame = self.capture_frame(camera_id)
        if frame is not None:
            try:
                cv2.imwrite(filepath, frame)
                logger.info(f"Saved frame to: {filepath}")
                return True
            except Exception as e:
                logger.error(f"Error saving frame to {filepath}: {str(e)}")
                return False
        return False
    
    def get_camera_info(self, camera_id: str) -> Optional[dict]:
        """
        Get information about a connected camera.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Camera information dictionary, or None if not found
        """
        if camera_id in self.cameras:
            return self.cameras[camera_id]['info']
        return None
    
    def disconnect_camera(self, camera_id: str):
        """
        Disconnect from a camera.
        
        Args:
            camera_id: Camera identifier
        """
        if camera_id in self.cameras:
            self.cameras[camera_id]['capture'].release()
            del self.cameras[camera_id]
            logger.info(f"Disconnected camera: {camera_id}")
    
    def disconnect_all(self):
        """Disconnect from all cameras."""
        for camera_id in list(self.cameras.keys()):
            self.disconnect_camera(camera_id)


class SimpleCamera:
    """Simplified camera interface for basic usage."""
    
    def __init__(self, device_id: int = 0):
        """
        Initialize camera with device ID.
        
        Args:
            device_id: Camera device ID (default: 0)
        """
        self.device_id = device_id
        self.cap = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to the camera.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.try:
            cap = cv2.VideoCapture(self.device_id)
        except Exception as e:
            print(f"Error creating VideoCapture: {e}")
            return None
            if self.cap.isOpened():
                self.connected = True
                logger.info(f"Connected to camera device {self.device_id}")
                return True
            else:
                logger.error(f"Failed to open camera device {self.device_id}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to camera: {str(e)}")
            return False
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        
        Returns:
            Captured frame as numpy array, or None if failed
        """
        if not self.connected or self.cap is None:
            logger.error("Camera not connected")
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                logger.warning("Failed to capture frame")
                return None
        except Exception as e:
            logger.error(f"Error capturing frame: {str(e)}")
            return None
    
    def disconnect(self):
        """Disconnect from the camera."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.connected = False
            logger.info("Camera disconnected")


def test_camera():
    """Test function for camera functionality."""
    logger.info("Testing camera functionality...")
    
    # Test simple camera
    camera = SimpleCamera()
    if camera.connect():
        frame = camera.capture()
        if frame is not None:
            logger.info(f"Captured frame: {frame.shape}")
            cv2.imwrite("test_capture.jpg", frame)
            logger.info("Saved test image to test_capture.jpg")
        camera.disconnect()
    
    # Test camera manager
    manager = CameraManager()
    detected = manager.detect_cameras()
    logger.info(f"Detected {len(detected)} cameras")
    
    for camera_info in detected:
        if manager.connect_camera(camera_info['id'], camera_info):
            frame = manager.capture_frame(camera_info['id'])
            if frame is not None:
                logger.info(f"Captured frame from {camera_info['id']}: {frame.shape}")
            manager.disconnect_camera(camera_info['id'])


if __name__ == "__main__":
    test_camera()