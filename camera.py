"""
Jetson Orin Camera Integration Module

This module provides a unified interface for capturing images from various camera types:
- USB webcams
- CSI cameras (Camera Serial Interface)
- IP cameras (Network cameras)

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import cv2
import numpy as np
import requests
import logging
import time
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse

# Import YOLO detector if available
try:
    from yolo_detector import YOLODetector, YOLOError
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLO detector not available. Install ultralytics for object detection features.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraError(Exception):
    """Custom exception for camera-related errors"""
    pass


class JetsonCamera:
    """
    Unified camera interface for Jetson Orin platform
    Supports USB, CSI, and IP cameras with plug-and-play functionality
    """
    
    def __init__(self, camera_id: int = 0, camera_type: str = "usb", 
                 ip_url: str = None, width: int = 1920, height: int = 1080, fps: int = 30,
                 enable_yolo: bool = False, yolo_model: str = "yolov8n.pt", 
                 yolo_confidence: float = 0.5):
        """
        Initialize camera interface
        
        Args:
            camera_id: Camera device ID (for USB/CSI cameras)
            camera_type: Type of camera ("usb", "csi", "ip")
            ip_url: URL for IP camera (required if camera_type="ip")
            width: Frame width
            height: Frame height
            fps: Frames per second
            enable_yolo: Enable YOLO object detection
            yolo_model: YOLO model path/name
            yolo_confidence: YOLO confidence threshold
        """
        self.camera_id = camera_id
        self.camera_type = camera_type.lower()
        self.ip_url = ip_url
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.is_connected = False
        
        # YOLO detection setup
        self.enable_yolo = enable_yolo
        self.yolo_detector = None
        if self.enable_yolo and YOLO_AVAILABLE:
            try:
                self.yolo_detector = YOLODetector(
                    model_path=yolo_model,
                    confidence_threshold=yolo_confidence
                )
                logger.info("YOLO detector initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize YOLO detector: {e}")
                self.enable_yolo = False
        elif self.enable_yolo and not YOLO_AVAILABLE:
            logger.warning("YOLO requested but not available. Install ultralytics package.")
            self.enable_yolo = False
        
        # Validate camera type
        if self.camera_type not in ["usb", "csi", "ip"]:
            raise CameraError(f"Unsupported camera type: {camera_type}")
        
        # Validate IP URL if IP camera
        if self.camera_type == "ip" and not ip_url:
            raise CameraError("IP URL required for IP camera type")
    
    def connect(self) -> bool:
        """
        Connect to the camera based on type
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.camera_type == "usb":
                return self._connect_usb()
            elif self.camera_type == "csi":
                return self._connect_csi()
            elif self.camera_type == "ip":
                return self._connect_ip()
        except Exception as e:
            logger.error(f"Failed to connect to {self.camera_type} camera: {e}")
            return False
    
    def _connect_usb(self) -> bool:
        """Connect to USB camera"""
        logger.info(f"Connecting to USB camera {self.camera_id}")
        
        # Try different backends for better compatibility
        backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(self.camera_id, backend)
                if self.cap.isOpened():
                    # Set camera properties
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                    
                    # Test frame capture
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        self.is_connected = True
                        logger.info(f"USB camera {self.camera_id} connected successfully")
                        return True
                    else:
                        self.cap.release()
            except Exception as e:
                logger.warning(f"Backend {backend} failed: {e}")
                continue
        
        logger.error(f"Failed to connect to USB camera {self.camera_id}")
        return False
    
    def _connect_csi(self) -> bool:
        """Connect to CSI camera using GStreamer pipeline"""
        logger.info(f"Connecting to CSI camera {self.camera_id}")
        
        # GStreamer pipeline for CSI camera on Jetson
        gst_pipeline = (
            f"nvarguscamerasrc sensor-id={self.camera_id} ! "
            f"video/x-raw(memory:NVMM), width={self.width}, height={self.height}, "
            f"format=NV12, framerate={self.fps}/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, width=1920, height=1080, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink"
        )
        
        try:
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            if self.cap.isOpened():
                # Test frame capture
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_connected = True
                    logger.info(f"CSI camera {self.camera_id} connected successfully")
                    return True
                else:
                    self.cap.release()
        except Exception as e:
            logger.error(f"CSI camera connection failed: {e}")
        
        logger.error(f"Failed to connect to CSI camera {self.camera_id}")
        return False
    
    def _connect_ip(self) -> bool:
        """Connect to IP camera"""
        logger.info(f"Connecting to IP camera at {self.ip_url}")
        
        try:
            # Test IP camera accessibility
            response = requests.get(self.ip_url, timeout=5)
            if response.status_code == 200:
                self.cap = cv2.VideoCapture(self.ip_url)
                if self.cap.isOpened():
                    # Test frame capture
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        self.is_connected = True
                        logger.info(f"IP camera connected successfully")
                        return True
                    else:
                        self.cap.release()
        except Exception as e:
            logger.error(f"IP camera connection failed: {e}")
        
        logger.error(f"Failed to connect to IP camera at {self.ip_url}")
        return False
    
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame from the camera
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame)
        """
        if not self.is_connected or not self.cap:
            logger.error("Camera not connected. Call connect() first.")
            return False, None
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return True, frame
            else:
                logger.warning("Failed to capture frame")
                return False, None
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return False, None
    
    def capture_multiple_frames(self, count: int = 5, delay: float = 0.1) -> list:
        """
        Capture multiple frames with delay
        
        Args:
            count: Number of frames to capture
            delay: Delay between captures in seconds
        
        Returns:
            list: List of captured frames
        """
        frames = []
        for i in range(count):
            ret, frame = self.capture_frame()
            if ret:
                frames.append(frame)
                logger.info(f"Captured frame {i+1}/{count}")
            else:
                logger.warning(f"Failed to capture frame {i+1}/{count}")
            
            if delay > 0 and i < count - 1:
                time.sleep(delay)
        
        return frames
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get camera information and properties
        
        Returns:
            Dict: Camera properties and info
        """
        if not self.is_connected or not self.cap:
            return {"error": "Camera not connected"}
        
        info = {
            "camera_type": self.camera_type,
            "camera_id": self.camera_id,
            "is_connected": self.is_connected,
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
        }
        
        if self.camera_type == "ip":
            info["ip_url"] = self.ip_url
        
        return info
    
    def save_frame(self, filename: str) -> bool:
        """
        Capture and save a frame to file
        
        Args:
            filename: Output filename
        
        Returns:
            bool: True if successful, False otherwise
        """
        ret, frame = self.capture_frame()
        if ret:
            try:
                cv2.imwrite(filename, frame)
                logger.info(f"Frame saved to {filename}")
                return True
            except Exception as e:
                logger.error(f"Failed to save frame: {e}")
                return False
        return False
    
    def disconnect(self):
        """Disconnect and release camera resources"""
        if self.cap:
            self.cap.release()
            self.is_connected = False
            logger.info(f"{self.camera_type.upper()} camera disconnected")
    
    def capture_frame_with_detection(self, annotate: bool = True, save_results: bool = False,
                                   output_path: Optional[str] = None) -> Tuple[bool, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Capture a frame and perform YOLO object detection
        
        Args:
            annotate: Whether to draw bounding boxes on the frame
            save_results: Whether to save detection results
            output_path: Path to save detection results
        
        Returns:
            Tuple[bool, Optional[np.ndarray], Optional[Dict]]: (success, frame/annotated_frame, detection_results)
        """
        if not self.enable_yolo or not self.yolo_detector:
            logger.warning("YOLO detection not enabled or not available")
            ret, frame = self.capture_frame()
            return ret, frame, None
        
        # Capture frame
        ret, frame = self.capture_frame()
        if not ret or frame is None:
            return False, None, None
        
        try:
            # Perform detection
            results = self.yolo_detector.detect(
                frame, 
                annotate=annotate, 
                save_results=save_results,
                output_path=output_path
            )
            
            return True, results['annotated_image'], results
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return ret, frame, None
    
    def get_yolo_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get YOLO detection statistics
        
        Returns:
            Dict: YOLO statistics or None if YOLO not enabled
        """
        if self.enable_yolo and self.yolo_detector:
            return self.yolo_detector.get_statistics()
        return None
    
    def set_yolo_confidence(self, confidence: float):
        """
        Set YOLO confidence threshold
        
        Args:
            confidence: New confidence threshold (0.0-1.0)
        """
        if self.enable_yolo and self.yolo_detector:
            self.yolo_detector.set_confidence_threshold(confidence)
        else:
            logger.warning("YOLO detection not enabled")
    
    def enable_yolo_detection(self, model_path: str = "yolov8n.pt", confidence: float = 0.5):
        """
        Enable YOLO detection on this camera
        
        Args:
            model_path: Path to YOLO model
            confidence: Confidence threshold
        """
        if not YOLO_AVAILABLE:
            logger.error("YOLO not available. Install ultralytics package.")
            return False
        
        try:
            self.yolo_detector = YOLODetector(
                model_path=model_path,
                confidence_threshold=confidence
            )
            self.enable_yolo = True
            logger.info("YOLO detection enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable YOLO detection: {e}")
            return False
    
    def disable_yolo_detection(self):
        """Disable YOLO detection"""
        self.enable_yolo = False
        self.yolo_detector = None
        logger.info("YOLO detection disabled")
    
    def filter_detections_by_class(self, detections: List[Dict[str, Any]], 
                                 target_classes: List[str]) -> List[Dict[str, Any]]:
        """
        Filter detections by class names
        
        Args:
            detections: List of detection results
            target_classes: List of class names to keep
            
        Returns:
            Filtered detections
        """
        if self.enable_yolo and self.yolo_detector:
            return self.yolo_detector.filter_detections_by_class(detections, target_classes)
        return []
    
    def count_objects_by_class(self, detections: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count detected objects by class
        
        Args:
            detections: List of detection results
            
        Returns:
            Dictionary with class counts
        """
        if self.enable_yolo and self.yolo_detector:
            return self.yolo_detector.count_objects_by_class(detections)
        return {}
    
    def __del__(self):
        """Destructor to ensure proper cleanup"""
        self.disconnect()


def detect_cameras() -> Dict[str, list]:
    """
    Detect available cameras on the system
    
    Returns:
        Dict: Dictionary with detected camera types and IDs
    """
    detected = {"usb": [], "csi": []}
    
    # Detect USB cameras
    logger.info("Detecting USB cameras...")
    for i in range(10):  # Check first 10 camera indices
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                detected["usb"].append(i)
                logger.info(f"USB camera detected at index {i}")
            cap.release()
    
    # Detect CSI cameras (try common indices)
    logger.info("Detecting CSI cameras...")
    for i in range(2):  # Most Jetson boards have 0-1 CSI ports
        gst_pipeline = (
            f"nvarguscamerasrc sensor-id={i} ! "
            "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
            "nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! "
            "video/x-raw, format=BGR ! appsink"
        )
        
        try:
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    detected["csi"].append(i)
                    logger.info(f"CSI camera detected at sensor-id {i}")
                cap.release()
        except Exception:
            continue
    
    return detected


# Example usage and testing functions
def test_camera(camera_type: str = "usb", camera_id: int = 0, ip_url: str = None):
    """
    Test camera functionality
    
    Args:
        camera_type: Type of camera to test
        camera_id: Camera ID
        ip_url: IP camera URL (if applicable)
    """
    logger.info(f"Testing {camera_type} camera...")
    
    try:
        # Initialize camera
        camera = JetsonCamera(
            camera_id=camera_id,
            camera_type=camera_type,
            ip_url=ip_url
        )
        
        # Connect to camera
        if camera.connect():
            # Get camera info
            info = camera.get_camera_info()
            logger.info(f"Camera info: {info}")
            
            # Capture a test frame
            ret, frame = camera.capture_frame()
            if ret:
                logger.info(f"Test frame captured: {frame.shape}")
                
                # Save test frame
                test_filename = f"test_frame_{camera_type}_{int(time.time())}.jpg"
                camera.save_frame(test_filename)
            else:
                logger.error("Failed to capture test frame")
        else:
            logger.error(f"Failed to connect to {camera_type} camera")
        
        # Cleanup
        camera.disconnect()
        
    except Exception as e:
        logger.error(f"Camera test failed: {e}")


if __name__ == "__main__":
    # Detect available cameras
    detected_cameras = detect_cameras()
    print(f"Detected cameras: {detected_cameras}")
    
    # Test USB camera if available
    if detected_cameras["usb"]:
        test_camera("usb", detected_cameras["usb"][0])
    
    # Test CSI camera if available
    if detected_cameras["csi"]:
        test_camera("csi", detected_cameras["csi"][0])