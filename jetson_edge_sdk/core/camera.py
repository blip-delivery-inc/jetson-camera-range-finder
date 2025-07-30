"""
Camera management module for Jetson Edge SDK
Supports both CSI and USB cameras with OpenCV backend
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Optional, Tuple, Callable, Any
from .config import CameraConfig


class CameraManager:
    """Manages camera operations for Jetson Nano Orin"""
    
    def __init__(self, config: CameraConfig):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_callback: Optional[Callable] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
    def _get_gstreamer_pipeline(self) -> str:
        """
        Generate GStreamer pipeline for CSI camera on Jetson
        This provides better performance than standard OpenCV capture
        """
        return (
            f"nvarguscamerasrc sensor-id={self.config.device_id} ! "
            f"video/x-raw(memory:NVMM), "
            f"width=(int){self.config.capture_width}, "
            f"height=(int){self.config.capture_height}, "
            f"framerate=(fraction){self.config.fps}/1 ! "
            f"nvvidconv flip-method={self.config.flip_method} ! "
            f"video/x-raw, "
            f"width=(int){self.config.width}, "
            f"height=(int){self.config.height}, "
            f"format=(string)BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=(string)BGR ! appsink"
        )
    
    def initialize(self, use_csi: bool = True) -> bool:
        """
        Initialize camera connection
        
        Args:
            use_csi: True for CSI camera, False for USB camera
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if use_csi:
                # Try CSI camera with GStreamer pipeline
                pipeline = self._get_gstreamer_pipeline()
                self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                self.logger.info(f"Initializing CSI camera with pipeline: {pipeline}")
            else:
                # USB camera
                self.cap = cv2.VideoCapture(self.config.device_id)
                self.logger.info(f"Initializing USB camera on device {self.config.device_id}")
                
                # Set USB camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
                
                # Set format if supported
                if self.config.format == "MJPG":
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            
            if not self.cap or not self.cap.isOpened():
                self.logger.error("Failed to open camera")
                return False
                
            # Test frame capture
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.logger.error("Failed to capture test frame")
                return False
                
            self.logger.info(f"Camera initialized successfully. Frame size: {frame.shape}")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    def start_capture(self, frame_callback: Optional[Callable] = None) -> bool:
        """
        Start continuous frame capture in background thread
        
        Args:
            frame_callback: Optional callback function to process each frame
            
        Returns:
            bool: True if capture started successfully
        """
        if not self.cap or not self.cap.isOpened():
            self.logger.error("Camera not initialized")
            return False
        
        if self.is_running:
            self.logger.warning("Capture already running")
            return True
        
        self.frame_callback = frame_callback
        self.is_running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        self.logger.info("Camera capture started")
        return True
    
    def _capture_loop(self) -> None:
        """Main capture loop running in background thread"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.logger.warning("Failed to capture frame")
                    continue
                
                # Store latest frame
                with self._frame_lock:
                    self._latest_frame = frame.copy()
                
                # Call user callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        self.logger.error(f"Frame callback error: {e}")
                        
            except Exception as e:
                self.logger.error(f"Capture loop error: {e}")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest captured frame
        
        Returns:
            numpy.ndarray: Latest frame or None if no frame available
        """
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame (blocking)
        
        Returns:
            numpy.ndarray: Captured frame or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            self.logger.error("Camera not initialized")
            return None
        
        ret, frame = self.cap.read()
        if ret and frame is not None:
            return frame
        else:
            self.logger.error("Failed to capture single frame")
            return None
    
    def save_frame(self, frame: np.ndarray, filename: str) -> bool:
        """
        Save frame to file
        
        Args:
            frame: Frame to save
            filename: Output filename
            
        Returns:
            bool: True if saved successfully
        """
        try:
            success = cv2.imwrite(filename, frame)
            if success:
                self.logger.info(f"Frame saved to {filename}")
            else:
                self.logger.error(f"Failed to save frame to {filename}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return False
    
    def stop_capture(self) -> None:
        """Stop continuous capture"""
        if self.is_running:
            self.is_running = False
            if self._capture_thread and self._capture_thread.is_alive():
                self._capture_thread.join(timeout=2.0)
            self.logger.info("Camera capture stopped")
    
    def release(self) -> None:
        """Release camera resources"""
        self.stop_capture()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.logger.info("Camera resources released")
    
    def get_camera_info(self) -> dict:
        """
        Get camera information and current settings
        
        Returns:
            dict: Camera information
        """
        if not self.cap or not self.cap.isOpened():
            return {"status": "not_initialized"}
        
        info = {
            "status": "initialized",
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "backend": self.cap.getBackendName(),
            "is_capturing": self.is_running
        }
        
        return info
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()