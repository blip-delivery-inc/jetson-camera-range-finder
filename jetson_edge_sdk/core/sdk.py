"""
Main SDK class for Jetson Edge SDK
Provides unified interface for camera and range finder operations
"""

import logging
import time
import os
from typing import Optional, Callable, Dict, Any
from .config import Config
from .camera import CameraManager
from .range_finder import RangeFinderManager, ScanData
import numpy as np


class JetsonEdgeSDK:
    """
    Main SDK class that orchestrates camera and range finder operations
    
    Simple usage:
        sdk = JetsonEdgeSDK()
        sdk.initialize()
        sdk.start()
        
        # Get data
        frame = sdk.get_camera_frame()
        scan = sdk.get_range_scan()
        
        sdk.stop()
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the SDK
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.camera: Optional[CameraManager] = None
        self.range_finder: Optional[RangeFinderManager] = None
        self.is_initialized = False
        self.is_running = False
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create data output directory
        os.makedirs(self.config.data_output_dir, exist_ok=True)
        
        self.logger.info("Jetson Edge SDK initialized")
    
    def initialize(self, use_csi_camera: bool = True) -> bool:
        """
        Initialize all enabled components
        
        Args:
            use_csi_camera: True for CSI camera, False for USB camera
            
        Returns:
            bool: True if initialization successful
        """
        success = True
        
        try:
            # Initialize camera if enabled
            if self.config.enable_camera:
                self.camera = CameraManager(self.config.camera)
                if not self.camera.initialize(use_csi=use_csi_camera):
                    self.logger.error("Camera initialization failed")
                    success = False
                else:
                    self.logger.info("Camera initialized successfully")
            
            # Initialize range finder if enabled
            if self.config.enable_range_finder:
                self.range_finder = RangeFinderManager(self.config.range_finder)
                if not self.range_finder.initialize():
                    self.logger.error("Range finder initialization failed")
                    success = False
                else:
                    self.logger.info("Range finder initialized successfully")
            
            self.is_initialized = success
            
            if success:
                self.logger.info("All components initialized successfully")
            else:
                self.logger.error("Some components failed to initialize")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            return False
    
    def start(self, 
              frame_callback: Optional[Callable] = None,
              scan_callback: Optional[Callable] = None) -> bool:
        """
        Start all operations
        
        Args:
            frame_callback: Optional callback for camera frames
            scan_callback: Optional callback for range finder scans
            
        Returns:
            bool: True if started successfully
        """
        if not self.is_initialized:
            self.logger.error("SDK not initialized. Call initialize() first.")
            return False
        
        if self.is_running:
            self.logger.warning("SDK already running")
            return True
        
        success = True
        
        try:
            # Start camera capture
            if self.camera:
                if not self.camera.start_capture(frame_callback):
                    self.logger.error("Failed to start camera capture")
                    success = False
            
            # Start range finder scanning
            if self.range_finder:
                if not self.range_finder.start_scan(scan_callback):
                    self.logger.error("Failed to start range finder scan")
                    success = False
            
            self.is_running = success
            
            if success:
                self.logger.info("All operations started successfully")
            else:
                self.logger.error("Some operations failed to start")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Start error: {e}")
            return False
    
    def stop(self) -> None:
        """Stop all operations"""
        if not self.is_running:
            return
        
        try:
            # Stop camera capture
            if self.camera:
                self.camera.stop_capture()
            
            # Stop range finder scanning
            if self.range_finder:
                self.range_finder.stop_scan()
            
            self.is_running = False
            self.logger.info("All operations stopped")
            
        except Exception as e:
            self.logger.error(f"Stop error: {e}")
    
    def release(self) -> None:
        """Release all resources"""
        self.stop()
        
        try:
            if self.camera:
                self.camera.release()
                self.camera = None
            
            if self.range_finder:
                self.range_finder.release()
                self.range_finder = None
            
            self.is_initialized = False
            self.logger.info("All resources released")
            
        except Exception as e:
            self.logger.error(f"Release error: {e}")
    
    # Camera methods
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Get latest camera frame
        
        Returns:
            numpy.ndarray: Latest frame or None if not available
        """
        if self.camera:
            return self.camera.get_frame()
        return None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame (blocking)
        
        Returns:
            numpy.ndarray: Captured frame or None if failed
        """
        if self.camera:
            return self.camera.capture_single_frame()
        return None
    
    def save_camera_frame(self, filename: Optional[str] = None) -> bool:
        """
        Save current camera frame to file
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            bool: True if saved successfully
        """
        if not self.camera:
            return False
        
        frame = self.camera.get_frame()
        if frame is None:
            return False
        
        if filename is None:
            timestamp = int(time.time() * 1000)
            filename = os.path.join(self.config.data_output_dir, f"frame_{timestamp}.jpg")
        
        return self.camera.save_frame(frame, filename)
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get camera information"""
        if self.camera:
            return self.camera.get_camera_info()
        return {"status": "not_available"}
    
    # Range finder methods
    def get_range_scan(self) -> Optional[ScanData]:
        """
        Get latest range finder scan
        
        Returns:
            ScanData: Latest scan or None if not available
        """
        if self.range_finder:
            return self.range_finder.get_latest_scan()
        return None
    
    def get_distance_at_angle(self, angle: float) -> Optional[float]:
        """
        Get distance measurement at specific angle
        
        Args:
            angle: Target angle in degrees
            
        Returns:
            float: Distance in meters or None if not available
        """
        if self.range_finder:
            return self.range_finder.get_distance_at_angle(angle)
        return None
    
    def get_obstacle_map(self, resolution: float = 1.0) -> Dict[float, float]:
        """
        Get obstacle map with specified resolution
        
        Args:
            resolution: Angular resolution in degrees
            
        Returns:
            dict: Mapping of angle to distance
        """
        if self.range_finder:
            return self.range_finder.get_obstacle_map(resolution)
        return {}
    
    def get_range_finder_info(self) -> Dict[str, Any]:
        """Get range finder information"""
        if self.range_finder:
            return self.range_finder.get_device_info()
        return {"status": "not_available"}
    
    # Utility methods
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        
        Returns:
            dict: System status information
        """
        status = {
            "sdk_version": "1.0.0",
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "timestamp": time.time(),
            "camera": self.get_camera_info(),
            "range_finder": self.get_range_finder_info(),
            "config": {
                "data_output_dir": self.config.data_output_dir,
                "camera_enabled": self.config.enable_camera,
                "range_finder_enabled": self.config.enable_range_finder
            }
        }
        
        return status
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        self.config.save_to_file(config_path)
    
    def wait_for_data(self, timeout: float = 5.0) -> bool:
        """
        Wait for both camera and range finder data to be available
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if data is available
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            camera_ready = not self.config.enable_camera or self.get_camera_frame() is not None
            range_ready = not self.config.enable_range_finder or self.get_range_scan() is not None
            
            if camera_ready and range_ready:
                return True
            
            time.sleep(0.1)
        
        return False
    
    # Context manager support
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()