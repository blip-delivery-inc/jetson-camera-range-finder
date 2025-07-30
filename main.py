#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Main Example Script

This script demonstrates the integration of camera and LIDAR sensors
on the NVIDIA Jetson Orin platform. It provides examples of:
- Camera detection and image capture
- LIDAR detection and range data acquisition
- Data logging and visualization
- Error handling and device management

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
import cv2
from datetime import datetime
from pathlib import Path
from threading import Lock

# Import SDK modules
from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, detect_lidar_devices, LidarType, LidarError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('jetson_sdk.log')
    ]
)
logger = logging.getLogger(__name__)


class JetsonSDK:
    """
    Main SDK class that orchestrates camera and LIDAR operations
    """
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize the Jetson SDK
        
        Args:
            output_dir: Directory to save captured data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Validate output directory is writable
        try:
            test_file = self.output_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise RuntimeError(f"Output directory is not writable: {output_dir}. Error: {e}")
        
        # Device instances
        self.camera = None
        self.lidar = None
        
        # Data collection
        self.is_running = False
        self.data_thread = None
        self.collected_data = []
        
        # Statistics (thread-safe)
        self.stats_lock = Lock()
        self.stats = {
            "images_captured": 0,
            "lidar_scans": 0,
            "errors": 0,
            "start_time": None,
            "runtime": 0
        }
        
        logger.info(f"Jetson SDK initialized. Output directory: {self.output_dir}")
    
    def detect_hardware(self) -> dict:
        """
        Detect available cameras and LIDAR devices
        
        Returns:
            dict: Detected hardware information
        """
        logger.info("Detecting available hardware...")
        
        # Detect cameras
        cameras = detect_cameras()
        logger.info(f"Detected cameras: {cameras}")
        
        # Detect LIDAR devices
        lidars = detect_lidar_devices()
        logger.info(f"Detected LIDAR devices: {lidars}")
        
        hardware = {
            "cameras": cameras,
            "lidars": lidars,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save hardware detection results
        with open(self.output_dir / "hardware_detection.json", "w") as f:
            json.dump(hardware, f, indent=2)
        
        return hardware
    
    def setup_camera(self, camera_type: str = "usb", camera_id: int = 0, 
                    ip_url: str = None) -> bool:
        """
        Setup and connect to camera
        
        Args:
            camera_type: Type of camera ("usb", "csi", "ip")
            camera_id: Camera device ID
            ip_url: IP camera URL (if applicable)
        
        Returns:
            bool: True if setup successful
        """
        try:
            logger.info(f"Setting up {camera_type} camera...")
            
            self.camera = JetsonCamera(
                camera_id=camera_id,
                camera_type=camera_type,
                ip_url=ip_url,
                width=1920,
                height=1080,
                fps=30
            )
            
            if self.camera.connect():
                info = self.camera.get_camera_info()
                logger.info(f"Camera connected: {info}")
                return True
            else:
                logger.error("Failed to connect to camera")
                return False
                
        except CameraError as e:
            logger.error(f"Camera setup error: {e}")
            return False
    
    def setup_lidar(self, lidar_type: str = "generic_serial", 
                   port: str = "/dev/ttyUSB0", baudrate: int = 115200,
                   ip_address: str = None) -> bool:
        """
        Setup and connect to LIDAR
        
        Args:
            lidar_type: Type of LIDAR
            port: Serial port
            baudrate: Communication baudrate
            ip_address: IP address for network LIDAR
        
        Returns:
            bool: True if setup successful
        """
        try:
            logger.info(f"Setting up {lidar_type} LIDAR...")
            
            # Map string to enum
            lidar_type_map = {
                "rplidar": LidarType.RPLIDAR,
                "ydlidar": LidarType.YDLIDAR,
                "hokuyo_urg": LidarType.HOKUYO_URG,
                "sick_tim": LidarType.SICK_TIM,
                "generic_serial": LidarType.GENERIC_SERIAL,
                "generic_udp": LidarType.GENERIC_UDP
            }
            
            lidar_enum = lidar_type_map.get(lidar_type, LidarType.GENERIC_SERIAL)
            
            self.lidar = JetsonLidar(
                lidar_type=lidar_enum,
                port=port,
                baudrate=baudrate,
                ip_address=ip_address
            )
            
            if self.lidar.connect():
                info = self.lidar.get_device_info()
                logger.info(f"LIDAR connected: {info}")
                return True
            else:
                logger.error("Failed to connect to LIDAR")
                return False
                
        except LidarError as e:
            logger.error(f"LIDAR setup error: {e}")
            return False
    
    def capture_single_data(self) -> dict:
        """
        Capture a single set of camera and LIDAR data
        
        Returns:
            dict: Captured data with timestamps
        """
        timestamp = time.time()
        data = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "camera": None,
            "lidar": None,
            "errors": []
        }
        
        # Capture camera image
        if self.camera:
            try:
                ret, frame = self.camera.capture_frame()
                if ret:
                    # Save image
                    image_filename = f"image_{int(timestamp)}.jpg"
                    image_path = self.output_dir / image_filename
                    
                    cv2.imwrite(str(image_path), frame)
                    
                    data["camera"] = {
                        "filename": image_filename,
                        "shape": frame.shape,
                        "success": True
                    }
                    with self.stats_lock:
                        self.stats["images_captured"] += 1
                    logger.info(f"Image captured: {image_filename}")
                else:
                    data["errors"].append("Failed to capture camera frame")
                    with self.stats_lock:
                        self.stats["errors"] += 1
            except Exception as e:
                error_msg = f"Camera capture error: {e}"
                data["errors"].append(error_msg)
                logger.error(error_msg)
                with self.stats_lock:
                    self.stats["errors"] += 1
        
        # Capture LIDAR data
        if self.lidar:
            try:
                measurement = self.lidar.get_single_measurement()
                if measurement:
                    data["lidar"] = {
                        "angle": measurement.angle,
                        "distance": measurement.distance,
                        "quality": measurement.quality,
                        "timestamp": measurement.timestamp,
                        "success": True
                    }
                    logger.info(f"LIDAR measurement: {measurement.distance}mm at {measurement.angle}°")
                else:
                    data["errors"].append("Failed to get LIDAR measurement")
                    with self.stats_lock:
                        self.stats["errors"] += 1
            except Exception as e:
                error_msg = f"LIDAR capture error: {e}"
                data["errors"].append(error_msg)
                logger.error(error_msg)
                with self.stats_lock:
                    self.stats["errors"] += 1
        
        return data
    
    def start_continuous_capture(self, interval: float = 1.0, duration: float = None):
        """
        Start continuous data capture
        
        Args:
            interval: Time between captures in seconds
            duration: Total duration in seconds (None for infinite)
        """
        if self.is_running:
            logger.warning("Continuous capture already running")
            return
        
        self.is_running = True
        with self.stats_lock:
            self.stats["start_time"] = time.time()
        
        logger.info(f"Starting continuous capture (interval: {interval}s, duration: {duration}s)")
        
        def capture_loop():
            start_time = time.time()
            
            while self.is_running:
                try:
                    # Check duration limit
                    if duration and (time.time() - start_time) >= duration:
                        logger.info("Duration limit reached, stopping capture")
                        break
                    
                    # Capture data
                    data = self.capture_single_data()
                    self.collected_data.append(data)
                    
                    # Update statistics
                    with self.stats_lock:
                        self.stats["runtime"] = time.time() - self.stats["start_time"]
                    
                except Exception as e:
                    logger.error(f"Error in continuous capture: {e}")
                    with self.stats_lock:
                        self.stats["errors"] += 1
                        error_count = self.stats["errors"]
                    # Continue running unless it's a critical error
                    if error_count > 10:  # Stop after too many consecutive errors
                        logger.error("Too many capture errors, stopping continuous capture")
                        break
                
                # Wait for next capture
                time.sleep(interval)
            
            self.is_running = False
            logger.info("Continuous capture stopped")
        
        # Start capture thread
        self.data_thread = threading.Thread(target=capture_loop, daemon=True)
        self.data_thread.start()
    
    def stop_continuous_capture(self):
        """Stop continuous data capture"""
        if not self.is_running:
            logger.warning("No continuous capture running")
            return
        
        logger.info("Stopping continuous capture...")
        self.is_running = False
        
        if self.data_thread:
            self.data_thread.join(timeout=5.0)
        
        # Save collected data
        if self.collected_data:
            data_filename = f"capture_data_{int(time.time())}.json"
            with open(self.output_dir / data_filename, "w") as f:
                json.dump(self.collected_data, f, indent=2)
            
            logger.info(f"Saved {len(self.collected_data)} data points to {data_filename}")
    
    def get_statistics(self) -> dict:
        """
        Get capture statistics
        
        Returns:
            dict: Statistics information
        """
        with self.stats_lock:
            stats = self.stats.copy()
        
        if stats["start_time"]:
            stats["runtime"] = time.time() - stats["start_time"]
            
            # Calculate rates
            if stats["runtime"] > 0:
                stats["image_rate"] = stats["images_captured"] / stats["runtime"]
                stats["scan_rate"] = stats["lidar_scans"] / stats["runtime"]
                stats["error_rate"] = stats["errors"] / stats["runtime"]
        
        return stats
    
    def run_demo(self, duration: float = 30.0):
        """
        Run a demonstration of SDK capabilities
        
        Args:
            duration: Demo duration in seconds
        """
        logger.info(f"Starting SDK demonstration (duration: {duration}s)")
        
        # Detect hardware
        hardware = self.detect_hardware()
        
        # Setup camera if available
        camera_setup = False
        if hardware["cameras"]["usb"]:
            camera_setup = self.setup_camera("usb", hardware["cameras"]["usb"][0])
        elif hardware["cameras"]["csi"]:
            camera_setup = self.setup_camera("csi", hardware["cameras"]["csi"][0])
        
        # Setup LIDAR if available
        lidar_setup = False
        if hardware["lidars"]:
            device = hardware["lidars"][0]
            lidar_setup = self.setup_lidar(
                device.get("likely_type", "generic_serial"),
                device["port"]
            )
        
        if not camera_setup and not lidar_setup:
            logger.warning("No devices available for demonstration")
            return
        
        # Capture single data point
        logger.info("Capturing single data sample...")
        single_data = self.capture_single_data()
        print(f"Single capture result: {json.dumps(single_data, indent=2)}")
        
        # Run continuous capture
        logger.info("Starting continuous capture...")
        self.start_continuous_capture(interval=2.0, duration=duration)
        
        # Wait for completion
        while self.is_running:
            time.sleep(1.0)
            stats = self.get_statistics()
            print(f"Runtime: {stats['runtime']:.1f}s, Images: {stats['images_captured']}, Errors: {stats['errors']}")
        
        # Final statistics
        final_stats = self.get_statistics()
        logger.info(f"Demo completed. Final stats: {final_stats}")
        
        # Save final statistics
        with open(self.output_dir / "demo_statistics.json", "w") as f:
            json.dump(final_stats, f, indent=2)
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up SDK resources...")
        
        # Stop any running captures
        if hasattr(self, 'is_running') and self.is_running:
            self.stop_continuous_capture()
        
        # Disconnect devices
        if hasattr(self, 'camera') and self.camera:
            self.camera.disconnect()
        
        if hasattr(self, 'lidar') and self.lidar:
            self.lidar.disconnect()
        
        logger.info("SDK cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except AttributeError:
            # Handle case where object wasn't fully initialized
            pass


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Jetson Orin Integration SDK")
    parser.add_argument("--mode", choices=["demo", "detect", "single", "continuous"], 
                       default="demo", help="Operation mode")
    parser.add_argument("--duration", type=float, default=30.0, 
                       help="Duration for demo/continuous mode (seconds)")
    parser.add_argument("--interval", type=float, default=1.0, 
                       help="Capture interval for continuous mode (seconds)")
    parser.add_argument("--camera-type", choices=["usb", "csi", "ip"], 
                       default="usb", help="Camera type")
    parser.add_argument("--camera-id", type=int, default=0, 
                       help="Camera device ID")
    parser.add_argument("--camera-ip", type=str, 
                       help="IP camera URL")
    parser.add_argument("--lidar-type", 
                       choices=["rplidar", "ydlidar", "hokuyo_urg", "sick_tim", 
                               "generic_serial", "generic_udp"],
                       default="generic_serial", help="LIDAR type")
    parser.add_argument("--lidar-port", type=str, default="/dev/ttyUSB0", 
                       help="LIDAR serial port")
    parser.add_argument("--lidar-baudrate", type=int, default=115200, 
                       help="LIDAR baudrate")
    parser.add_argument("--output-dir", type=str, default="data", 
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Initialize SDK
    sdk = JetsonSDK(output_dir=args.output_dir)
    
    try:
        if args.mode == "detect":
            # Hardware detection only
            hardware = sdk.detect_hardware()
            print(json.dumps(hardware, indent=2))
            
        elif args.mode == "single":
            # Single capture
            # Setup devices
            if sdk.setup_camera(args.camera_type, args.camera_id, args.camera_ip):
                logger.info("Camera setup successful")
            
            if sdk.setup_lidar(args.lidar_type, args.lidar_port, args.lidar_baudrate):
                logger.info("LIDAR setup successful")
            
            # Capture data
            data = sdk.capture_single_data()
            print(json.dumps(data, indent=2))
            
        elif args.mode == "continuous":
            # Continuous capture
            # Setup devices
            sdk.setup_camera(args.camera_type, args.camera_id, args.camera_ip)
            sdk.setup_lidar(args.lidar_type, args.lidar_port, args.lidar_baudrate)
            
            # Start capture
            sdk.start_continuous_capture(args.interval, args.duration)
            
            # Monitor progress
            while sdk.is_running:
                time.sleep(1.0)
                stats = sdk.get_statistics()
                print(f"Runtime: {stats['runtime']:.1f}s, Images: {stats['images_captured']}, Errors: {stats['errors']}")
            
        else:  # demo mode
            # Run full demonstration
            sdk.run_demo(args.duration)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        sdk.cleanup()


if __name__ == "__main__":
    main()