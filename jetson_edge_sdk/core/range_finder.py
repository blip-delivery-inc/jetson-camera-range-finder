"""
Laser Range Finder management module for Jetson Edge SDK
Supports common LIDAR sensors via serial communication
"""

import serial
import threading
import time
import logging
import struct
import math
from typing import Optional, List, Tuple, Callable, Dict, Any
from dataclasses import dataclass
from .config import RangeFinderConfig


@dataclass
class RangeReading:
    """Single range measurement"""
    angle: float      # degrees
    distance: float   # meters
    quality: int      # signal quality (0-255)
    timestamp: float  # unix timestamp


@dataclass
class ScanData:
    """Complete scan data"""
    readings: List[RangeReading]
    scan_time: float
    timestamp: float


class RangeFinderManager:
    """Manages laser range finder operations"""
    
    def __init__(self, config: RangeFinderConfig):
        self.config = config
        self.serial_port: Optional[serial.Serial] = None
        self.is_running = False
        self.scan_callback: Optional[Callable] = None
        self._scan_thread: Optional[threading.Thread] = None
        self._latest_scan: Optional[ScanData] = None
        self._scan_lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
        # Protocol constants for common LIDAR sensors
        self.RPLIDAR_SYNC_BYTE = 0xA5
        self.RPLIDAR_RESPONSE_HEADER_SIZE = 7
        
    def initialize(self) -> bool:
        """
        Initialize serial connection to range finder
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.serial_port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            if not self.serial_port.is_open:
                self.logger.error("Failed to open serial port")
                return False
            
            # Clear any existing data in buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
            # Test communication
            if not self._test_communication():
                self.logger.warning("Communication test failed, but continuing...")
            
            self.logger.info(f"Range finder initialized on {self.config.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Range finder initialization failed: {e}")
            return False
    
    def _test_communication(self) -> bool:
        """Test basic communication with the range finder"""
        try:
            # Send stop command first
            self._send_command(b'\xA5\x25')
            time.sleep(0.1)
            
            # Send device info request (common command)
            self._send_command(b'\xA5\x50')
            time.sleep(0.1)
            
            # Try to read response
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.read(self.serial_port.in_waiting)
                self.logger.info(f"Communication test received {len(data)} bytes")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Communication test error: {e}")
            return False
    
    def _send_command(self, command: bytes) -> bool:
        """Send command to range finder"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(command)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Command send error: {e}")
            return False
    
    def start_scan(self, scan_callback: Optional[Callable] = None) -> bool:
        """
        Start continuous scanning
        
        Args:
            scan_callback: Optional callback function to process each scan
            
        Returns:
            bool: True if scan started successfully
        """
        if not self.serial_port or not self.serial_port.is_open:
            self.logger.error("Range finder not initialized")
            return False
        
        if self.is_running:
            self.logger.warning("Scan already running")
            return True
        
        # Send start scan command (RPLidar format)
        if not self._send_command(b'\xA5\x20'):
            self.logger.error("Failed to send start scan command")
            return False
        
        self.scan_callback = scan_callback
        self.is_running = True
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()
        
        self.logger.info("Range finder scan started")
        return True
    
    def _scan_loop(self) -> None:
        """Main scanning loop running in background thread"""
        scan_buffer = []
        
        while self.is_running:
            try:
                # Read scan data - this is a simplified implementation
                # Real implementation would depend on specific LIDAR protocol
                readings = self._read_scan_data()
                
                if readings:
                    scan_data = ScanData(
                        readings=readings,
                        scan_time=len(readings) * 0.001,  # Approximate scan time
                        timestamp=time.time()
                    )
                    
                    # Store latest scan
                    with self._scan_lock:
                        self._latest_scan = scan_data
                    
                    # Call user callback if provided
                    if self.scan_callback:
                        try:
                            self.scan_callback(scan_data)
                        except Exception as e:
                            self.logger.error(f"Scan callback error: {e}")
                
                time.sleep(0.01)  # Small delay to prevent overwhelming the system
                
            except Exception as e:
                self.logger.error(f"Scan loop error: {e}")
                time.sleep(0.1)
    
    def _read_scan_data(self) -> List[RangeReading]:
        """
        Read and parse scan data from serial port
        This is a simplified implementation - real implementation would 
        depend on specific LIDAR sensor protocol
        """
        readings = []
        
        try:
            if not self.serial_port or self.serial_port.in_waiting < 5:
                return readings
            
            # Read available data
            raw_data = self.serial_port.read(min(self.serial_port.in_waiting, 1000))
            
            # Simple parsing - in reality this would be much more complex
            # and depend on the specific LIDAR protocol
            for i in range(0, len(raw_data) - 4, 5):
                try:
                    # Mock parsing - replace with actual protocol parsing
                    angle = (i * 360.0 / len(raw_data)) % 360.0
                    distance_raw = struct.unpack('<H', raw_data[i:i+2])[0]
                    distance = distance_raw / 1000.0  # Convert to meters
                    quality = raw_data[i+2] if i+2 < len(raw_data) else 0
                    
                    # Filter readings within configured range
                    if self.config.min_range <= distance <= self.config.max_range:
                        reading = RangeReading(
                            angle=angle,
                            distance=distance,
                            quality=quality,
                            timestamp=time.time()
                        )
                        readings.append(reading)
                        
                except (struct.error, IndexError):
                    continue
            
        except Exception as e:
            self.logger.error(f"Scan data read error: {e}")
        
        return readings
    
    def get_latest_scan(self) -> Optional[ScanData]:
        """
        Get the latest scan data
        
        Returns:
            ScanData: Latest scan or None if no scan available
        """
        with self._scan_lock:
            return self._latest_scan
    
    def get_single_measurement(self, angle: float = 0.0) -> Optional[RangeReading]:
        """
        Get a single distance measurement at specified angle
        
        Args:
            angle: Target angle in degrees (0-360)
            
        Returns:
            RangeReading: Single measurement or None if failed
        """
        latest_scan = self.get_latest_scan()
        if not latest_scan or not latest_scan.readings:
            return None
        
        # Find closest reading to target angle
        closest_reading = min(
            latest_scan.readings,
            key=lambda r: abs(r.angle - angle)
        )
        
        return closest_reading
    
    def get_distance_at_angle(self, angle: float) -> Optional[float]:
        """
        Get distance measurement at specific angle
        
        Args:
            angle: Target angle in degrees
            
        Returns:
            float: Distance in meters or None if not available
        """
        reading = self.get_single_measurement(angle)
        return reading.distance if reading else None
    
    def get_obstacle_map(self, resolution: float = 1.0) -> Dict[float, float]:
        """
        Get obstacle map with specified angular resolution
        
        Args:
            resolution: Angular resolution in degrees
            
        Returns:
            dict: Mapping of angle to distance
        """
        obstacle_map = {}
        latest_scan = self.get_latest_scan()
        
        if not latest_scan or not latest_scan.readings:
            return obstacle_map
        
        # Group readings by angle bins
        for reading in latest_scan.readings:
            angle_bin = round(reading.angle / resolution) * resolution
            
            # Keep closest distance for each angle bin
            if angle_bin not in obstacle_map or reading.distance < obstacle_map[angle_bin]:
                obstacle_map[angle_bin] = reading.distance
        
        return obstacle_map
    
    def stop_scan(self) -> None:
        """Stop continuous scanning"""
        if self.is_running:
            self.is_running = False
            
            # Send stop command
            self._send_command(b'\xA5\x25')
            
            if self._scan_thread and self._scan_thread.is_alive():
                self._scan_thread.join(timeout=2.0)
            
            self.logger.info("Range finder scan stopped")
    
    def release(self) -> None:
        """Release range finder resources"""
        self.stop_scan()
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
        
        self.logger.info("Range finder resources released")
    
    def get_device_info(self) -> dict:
        """
        Get device information
        
        Returns:
            dict: Device information
        """
        info = {
            "port": self.config.port,
            "baudrate": self.config.baudrate,
            "is_connected": self.serial_port is not None and self.serial_port.is_open,
            "is_scanning": self.is_running,
            "max_range": self.config.max_range,
            "min_range": self.config.min_range,
            "scan_angle": self.config.scan_angle
        }
        
        return info
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()