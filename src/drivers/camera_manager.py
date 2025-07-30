"""
Camera Manager - Handles multiple camera streams
"""

import cv2
import threading
import time
import numpy as np
from typing import Dict, Any, Optional, List
from collections import deque
import logging

from utils.logger import LoggerMixin


class Camera:
    """Individual camera instance"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"Camera_{config['id']}")
        
        self.id = config['id']
        self.name = config['name']
        self.device_id = config['device_id']
        self.width = config['width']
        self.height = config['height']
        self.fps = config['fps']
        self.format = config['format']
        self.enabled = config['enabled']
        
        # Camera state
        self.cap = None
        self.running = False
        self.latest_frame = None
        self.frame_timestamp = None
        self.frame_count = 0
        self.fps_actual = 0.0
        
        # Threading
        self.lock = threading.Lock()
        self.thread = None
        
        # FPS calculation
        self.fps_times = deque(maxlen=30)
        
        if self.enabled:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.device_id}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            raise
    
    def start(self):
        """Start camera capture thread"""
        if not self.enabled or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, name=f"Camera_{self.id}")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("Camera capture started")
    
    def stop(self):
        """Stop camera capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.cap:
            self.cap.release()
        
        self.logger.info("Camera capture stopped")
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if ret:
                    with self.lock:
                        self.latest_frame = frame.copy()
                        self.frame_timestamp = time.time()
                        self.frame_count += 1
                    
                    # Calculate FPS
                    self.fps_times.append(time.time())
                    if len(self.fps_times) > 1:
                        time_diff = self.fps_times[-1] - self.fps_times[0]
                        if time_diff > 0:
                            self.fps_actual = (len(self.fps_times) - 1) / time_diff
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                time.sleep(1.0)
    
    def get_frame(self) -> Optional[Dict[str, Any]]:
        """Get latest frame with metadata"""
        with self.lock:
            if self.latest_frame is not None:
                return {
                    'frame': self.latest_frame.copy(),
                    'timestamp': self.frame_timestamp,
                    'frame_count': self.frame_count,
                    'fps': self.fps_actual,
                    'camera_id': self.id,
                    'camera_name': self.name
                }
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get camera status"""
        return {
            'id': self.id,
            'name': self.name,
            'enabled': self.enabled,
            'running': self.running,
            'frame_count': self.frame_count,
            'fps': self.fps_actual,
            'resolution': f"{self.width}x{self.height}",
            'connected': self.cap is not None and self.cap.isOpened() if self.cap else False
        }


class CameraManager(LoggerMixin):
    """Manages multiple camera instances"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cameras: Dict[str, Camera] = {}
        self.running = False
        
        # Initialize cameras
        self._initialize_cameras()
    
    def _initialize_cameras(self):
        """Initialize all configured cameras"""
        for device_config in self.config['devices']:
            if device_config['enabled']:
                try:
                    camera = Camera(device_config)
                    self.cameras[device_config['id']] = camera
                    self.logger.info(f"Camera {device_config['id']} initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize camera {device_config['id']}: {e}")
    
    def start(self):
        """Start all cameras"""
        self.running = True
        for camera in self.cameras.values():
            camera.start()
        self.logger.info(f"Started {len(self.cameras)} cameras")
    
    def stop(self):
        """Stop all cameras"""
        self.running = False
        for camera in self.cameras.values():
            camera.stop()
        self.logger.info("All cameras stopped")
    
    def get_frame(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get frame from specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame()
        return None
    
    def get_all_frames(self) -> Dict[str, Any]:
        """Get frames from all cameras"""
        frames = {}
        for camera_id, camera in self.cameras.items():
            frame_data = camera.get_frame()
            if frame_data:
                frames[camera_id] = frame_data
        return frames
    
    def get_camera_list(self) -> List[str]:
        """Get list of available camera IDs"""
        return list(self.cameras.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all cameras"""
        status = {
            'running': self.running,
            'total_cameras': len(self.cameras),
            'cameras': {}
        }
        
        for camera_id, camera in self.cameras.items():
            status['cameras'][camera_id] = camera.get_status()
        
        return status
    
    def shutdown(self):
        """Shutdown camera manager"""
        self.stop()
        self.logger.info("Camera manager shutdown complete")