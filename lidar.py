"""
Jetson Orin LIDAR Integration Module

This module provides interfaces for laser range finders (LIDAR) via:
- USB connection
- Serial connection (UART/RS232)
- Ethernet connection (for network-enabled LIDAR)

Supports common LIDAR protocols and models including:
- RPLidar series
- YDLidar series
- SICK TiM series
- Hokuyo URG series
- Generic NMEA-style range finders

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import serial
import serial.tools.list_ports
import socket
import struct
import time
import threading
import logging
import json
import math
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LidarError(Exception):
    """Custom exception for LIDAR-related errors"""
    pass


class LidarType(Enum):
    """Supported LIDAR types"""
    RPLIDAR = "rplidar"
    YDLIDAR = "ydlidar"
    SICK_TIM = "sick_tim"
    HOKUYO_URG = "hokuyo_urg"
    GENERIC_SERIAL = "generic_serial"
    GENERIC_UDP = "generic_udp"


@dataclass
class LidarPoint:
    """Single LIDAR measurement point"""
    angle: float  # Angle in degrees
    distance: float  # Distance in millimeters
    quality: int = 0  # Quality/intensity (0-255)
    timestamp: float = 0.0  # Timestamp


@dataclass
class LidarScan:
    """Complete LIDAR scan data"""
    points: List[LidarPoint]
    timestamp: float
    scan_id: int = 0
    rpm: float = 0.0  # Rotation speed


class JetsonLidar:
    """
    Unified LIDAR interface for Jetson Orin platform
    Supports various LIDAR types and connection methods
    """
    
    def __init__(self, lidar_type: LidarType = LidarType.GENERIC_SERIAL,
                 port: str = "/dev/ttyUSB0", baudrate: int = 115200,
                 ip_address: str = None, ip_port: int = 2111,
                 timeout: float = 1.0):
        """
        Initialize LIDAR interface
        
        Args:
            lidar_type: Type of LIDAR device
            port: Serial port path
            baudrate: Serial communication baudrate
            ip_address: IP address for network LIDAR
            ip_port: Network port for network LIDAR
            timeout: Communication timeout in seconds
        """
        # Validate LIDAR type
        if not isinstance(lidar_type, LidarType):
            raise LidarError(f"Invalid LIDAR type: {lidar_type}. Must be a LidarType enum value.")
        
        self.lidar_type = lidar_type
        self.port = port
        self.baudrate = baudrate
        self.ip_address = ip_address
        self.ip_port = ip_port
        self.timeout = timeout
        
        # Connection objects
        self.serial_conn = None
        self.socket_conn = None
        self.is_connected = False
        self.is_scanning = False
        
        # Data collection
        self.current_scan = []
        self.scan_thread = None
        self.scan_callback = None
        self.scan_id = 0
        
        # LIDAR-specific parameters
        self.motor_speed = 600  # RPM
        self.sample_rate = 2000  # Hz
        
    def connect(self) -> bool:
        """
        Connect to LIDAR device
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.lidar_type in [LidarType.RPLIDAR, LidarType.YDLIDAR, 
                                 LidarType.HOKUYO_URG, LidarType.GENERIC_SERIAL]:
                return self._connect_serial()
            elif self.lidar_type in [LidarType.SICK_TIM, LidarType.GENERIC_UDP]:
                return self._connect_network()
            else:
                raise LidarError(f"Unsupported LIDAR type: {self.lidar_type}")
        except Exception as e:
            logger.error(f"Failed to connect to LIDAR: {e}")
            return False
    
    def _connect_serial(self) -> bool:
        """Connect via serial interface"""
        logger.info(f"Connecting to {self.lidar_type.value} via {self.port}")
        
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            if self.serial_conn.is_open:
                # Send initialization commands based on LIDAR type
                if self._initialize_lidar():
                    self.is_connected = True
                    logger.info(f"LIDAR connected successfully via {self.port}")
                    return True
                else:
                    self.serial_conn.close()
                    return False
            
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            return False
        
        return False
    
    def _connect_network(self) -> bool:
        """Connect via network interface"""
        logger.info(f"Connecting to {self.lidar_type.value} at {self.ip_address}:{self.ip_port}")
        
        try:
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket_conn.settimeout(self.timeout)
            
            # Test connection
            test_data = b"test"
            self.socket_conn.sendto(test_data, (self.ip_address, self.ip_port))
            
            self.is_connected = True
            logger.info(f"Network LIDAR connected at {self.ip_address}:{self.ip_port}")
            return True
            
        except Exception as e:
            logger.error(f"Network connection failed: {e}")
            return False
    
    def _initialize_lidar(self) -> bool:
        """Initialize LIDAR with device-specific commands"""
        try:
            if self.lidar_type == LidarType.RPLIDAR:
                return self._init_rplidar()
            elif self.lidar_type == LidarType.YDLIDAR:
                return self._init_ydlidar()
            elif self.lidar_type == LidarType.HOKUYO_URG:
                return self._init_hokuyo()
            elif self.lidar_type == LidarType.GENERIC_SERIAL:
                return self._init_generic_serial()
            return True
        except Exception as e:
            logger.error(f"LIDAR initialization failed: {e}")
            return False
    
    def _init_rplidar(self) -> bool:
        """Initialize RPLidar"""
        # Stop any ongoing scan
        self.serial_conn.write(b'\xA5\x25')
        time.sleep(0.1)
        
        # Reset device
        self.serial_conn.write(b'\xA5\x40')
        time.sleep(2)
        
        # Get device info
        self.serial_conn.write(b'\xA5\x50')
        response = self.serial_conn.read(27)
        
        if len(response) >= 27:
            logger.info("RPLidar initialized successfully")
            return True
        return False
    
    def _init_ydlidar(self) -> bool:
        """Initialize YDLidar"""
        # Similar to RPLidar but with different commands
        self.serial_conn.write(b'\xA5\x65')  # Stop scan
        time.sleep(0.1)
        
        self.serial_conn.write(b'\xA5\x60')  # Get device info
        response = self.serial_conn.read(20)
        
        if len(response) >= 7:
            logger.info("YDLidar initialized successfully")
            return True
        return False
    
    def _init_hokuyo(self) -> bool:
        """Initialize Hokuyo URG series"""
        # Send SCIP2.0 commands
        self.serial_conn.write(b'VV\n')  # Version info
        response = self.serial_conn.read(100)
        
        if b'VEND' in response:
            logger.info("Hokuyo LIDAR initialized successfully")
            return True
        return False
    
    def _init_generic_serial(self) -> bool:
        """Initialize generic serial LIDAR"""
        # Just verify serial connection is working
        self.serial_conn.write(b'\r\n')
        time.sleep(0.1)
        if self.serial_conn.in_waiting > 0:
            self.serial_conn.read_all()
        logger.info("Generic serial LIDAR initialized")
        return True
    
    def start_scan(self, callback=None) -> bool:
        """
        Start continuous scanning
        
        Args:
            callback: Function to call with each scan (optional)
        
        Returns:
            bool: True if scan started successfully
        """
        if not self.is_connected:
            logger.error("LIDAR not connected")
            return False
        
        if self.is_scanning:
            logger.warning("Scan already in progress")
            return True
        
        self.scan_callback = callback
        self.is_scanning = True
        
        # Start scanning based on LIDAR type
        if self.lidar_type == LidarType.RPLIDAR:
            self._start_rplidar_scan()
        elif self.lidar_type == LidarType.YDLIDAR:
            self._start_ydlidar_scan()
        elif self.lidar_type == LidarType.HOKUYO_URG:
            self._start_hokuyo_scan()
        else:
            self._start_generic_scan()
        
        # Start data collection thread
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        
        logger.info("LIDAR scanning started")
        return True
    
    def _start_rplidar_scan(self):
        """Start RPLidar scanning"""
        # Express scan mode for better performance
        self.serial_conn.write(b'\xA5\x82\x05\x00\x00\x00\x00\x00\x22')
    
    def _start_ydlidar_scan(self):
        """Start YDLidar scanning"""
        self.serial_conn.write(b'\xA5\x60')  # Start scan
    
    def _start_hokuyo_scan(self):
        """Start Hokuyo scanning"""
        self.serial_conn.write(b'MD0044072500\n')  # Start measurement
    
    def _start_generic_scan(self):
        """Start generic scanning"""
        # Send a generic start command
        if self.serial_conn:
            self.serial_conn.write(b'START\n')
    
    def _scan_loop(self):
        """Main scanning loop running in separate thread"""
        while self.is_scanning:
            try:
                if self.lidar_type == LidarType.RPLIDAR:
                    scan_data = self._read_rplidar_data()
                elif self.lidar_type == LidarType.YDLIDAR:
                    scan_data = self._read_ydlidar_data()
                elif self.lidar_type == LidarType.HOKUYO_URG:
                    scan_data = self._read_hokuyo_data()
                else:
                    scan_data = self._read_generic_data()
                
                if scan_data and self.scan_callback:
                    self.scan_callback(scan_data)
                    
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                time.sleep(0.1)
    
    def _read_rplidar_data(self) -> Optional[LidarScan]:
        """Read data from RPLidar"""
        points = []
        
        while len(points) < 360 and self.is_scanning:
            try:
                # Read response descriptor
                descriptor = self.serial_conn.read(7)
                if len(descriptor) < 7:
                    continue
                
                # Parse measurement data
                start_flag = descriptor[0] & 0x1
                check_bit = (descriptor[0] & 0x2) >> 1
                
                if start_flag:
                    # New scan started
                    if points:
                        # Return completed scan
                        scan = LidarScan(
                            points=points,
                            timestamp=time.time(),
                            scan_id=self.scan_id
                        )
                        self.scan_id += 1
                        return scan
                    points = []
                
                # Extract angle and distance
                angle_q6 = ((descriptor[1] | (descriptor[2] << 8)) >> 1)
                angle = angle_q6 / 64.0
                
                distance_q2 = descriptor[3] | (descriptor[4] << 8)
                distance = distance_q2 / 4.0
                
                quality = descriptor[5] >> 2
                
                if distance > 0:
                    point = LidarPoint(
                        angle=angle,
                        distance=distance,
                        quality=quality,
                        timestamp=time.time()
                    )
                    points.append(point)
                
            except Exception as e:
                logger.warning(f"RPLidar data read error: {e}")
                continue
        
        return None
    
    def _read_ydlidar_data(self) -> Optional[LidarScan]:
        """Read data from YDLidar"""
        # Similar to RPLidar but with different packet format
        return self._read_generic_data()
    
    def _read_hokuyo_data(self) -> Optional[LidarScan]:
        """Read data from Hokuyo LIDAR"""
        try:
            line = self.serial_conn.readline().decode('ascii').strip()
            if line.startswith('MD'):
                # Parse Hokuyo SCIP format
                points = []
                data_lines = []
                
                # Read data lines
                while True:
                    data_line = self.serial_conn.readline().decode('ascii').strip()
                    if data_line == '':
                        break
                    data_lines.append(data_line)
                
                # Parse distance data
                for i, distance_str in enumerate(''.join(data_lines)):
                    if distance_str.isdigit():
                        distance = int(distance_str) * 1.0  # Convert to mm
                        angle = i * 0.25  # 0.25 degree resolution
                        
                        point = LidarPoint(
                            angle=angle,
                            distance=distance,
                            quality=255,
                            timestamp=time.time()
                        )
                        points.append(point)
                
                return LidarScan(
                    points=points,
                    timestamp=time.time(),
                    scan_id=self.scan_id
                )
        except Exception as e:
            logger.warning(f"Hokuyo data read error: {e}")
        
        return None
    
    def _read_generic_data(self) -> Optional[LidarScan]:
        """Read generic LIDAR data"""
        try:
            if self.serial_conn and self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                
                # Try to parse as comma-separated values: angle,distance
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            angle = float(parts[0])
                            distance = float(parts[1])
                            
                            point = LidarPoint(
                                angle=angle,
                                distance=distance,
                                quality=255,
                                timestamp=time.time()
                            )
                            
                            return LidarScan(
                                points=[point],
                                timestamp=time.time(),
                                scan_id=self.scan_id
                            )
                        except ValueError:
                            pass
            
        except Exception as e:
            logger.warning(f"Generic data read error: {e}")
        
        return None
    
    def get_single_measurement(self) -> Optional[LidarPoint]:
        """
        Get a single distance measurement
        
        Returns:
            LidarPoint: Single measurement point
        """
        if not self.is_connected:
            logger.error("LIDAR not connected")
            return None
        
        try:
            if self.lidar_type == LidarType.HOKUYO_URG:
                # Single measurement command
                self.serial_conn.write(b'GD0044072500\n')
                response = self.serial_conn.readline().decode('ascii').strip()
                
                if response and response.isdigit():
                    distance = int(response)
                    return LidarPoint(
                        angle=0.0,
                        distance=distance,
                        quality=255,
                        timestamp=time.time()
                    )
            else:
                # For other LIDAR types, try to read one data point
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    # Parse simple format: distance or angle,distance
                    try:
                        if ',' in data:
                            angle, distance = map(float, data.split(',')[:2])
                        else:
                            angle = 0.0
                            distance = float(data)
                        
                        return LidarPoint(
                            angle=angle,
                            distance=distance,
                            quality=255,
                            timestamp=time.time()
                        )
                    except ValueError:
                        pass
        
        except Exception as e:
            logger.error(f"Single measurement error: {e}")
        
        return None
    
    def stop_scan(self):
        """Stop continuous scanning"""
        self.is_scanning = False
        
        if self.scan_thread:
            self.scan_thread.join(timeout=2.0)
        
        # Send stop commands based on LIDAR type
        try:
            if self.lidar_type == LidarType.RPLIDAR:
                self.serial_conn.write(b'\xA5\x25')
            elif self.lidar_type == LidarType.YDLIDAR:
                self.serial_conn.write(b'\xA5\x65')
            elif self.lidar_type == LidarType.HOKUYO_URG:
                self.serial_conn.write(b'QT\n')
            else:
                if self.serial_conn:
                    self.serial_conn.write(b'STOP\n')
        except Exception as e:
            logger.warning(f"Stop scan command failed: {e}")
        
        logger.info("LIDAR scanning stopped")
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get LIDAR device information
        
        Returns:
            Dict: Device information
        """
        info = {
            "lidar_type": self.lidar_type.value,
            "port": self.port,
            "baudrate": self.baudrate,
            "is_connected": self.is_connected,
            "is_scanning": self.is_scanning,
        }
        
        if self.ip_address:
            info["ip_address"] = self.ip_address
            info["ip_port"] = self.ip_port
        
        return info
    
    def disconnect(self):
        """Disconnect from LIDAR"""
        self.stop_scan()
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            
        if self.socket_conn:
            self.socket_conn.close()
        
        self.is_connected = False
        logger.info("LIDAR disconnected")
    
    def __del__(self):
        """Destructor to ensure proper cleanup"""
        self.disconnect()


def detect_lidar_devices() -> List[Dict[str, str]]:
    """
    Detect available LIDAR devices
    
    Returns:
        List: List of detected LIDAR devices
    """
    devices = []
    
    # Detect serial devices
    logger.info("Detecting serial LIDAR devices...")
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        device_info = {
            "port": port.device,
            "description": port.description,
            "hwid": port.hwid,
            "type": "serial"
        }
        
        # Try to identify LIDAR type based on description/vendor
        description_lower = port.description.lower()
        if "rplidar" in description_lower or "slamtec" in description_lower:
            device_info["likely_type"] = "rplidar"
        elif "ydlidar" in description_lower:
            device_info["likely_type"] = "ydlidar"
        elif "hokuyo" in description_lower:
            device_info["likely_type"] = "hokuyo_urg"
        else:
            device_info["likely_type"] = "generic_serial"
        
        devices.append(device_info)
        logger.info(f"Serial device detected: {port.device} - {port.description}")
    
    return devices


def test_lidar(lidar_type: LidarType = LidarType.GENERIC_SERIAL, 
               port: str = "/dev/ttyUSB0", baudrate: int = 115200):
    """
    Test LIDAR functionality
    
    Args:
        lidar_type: Type of LIDAR to test
        port: Serial port
        baudrate: Communication baudrate
    """
    logger.info(f"Testing {lidar_type.value} LIDAR...")
    
    try:
        # Initialize LIDAR
        lidar = JetsonLidar(
            lidar_type=lidar_type,
            port=port,
            baudrate=baudrate
        )
        
        # Connect to LIDAR
        if lidar.connect():
            # Get device info
            info = lidar.get_device_info()
            logger.info(f"LIDAR info: {info}")
            
            # Test single measurement
            measurement = lidar.get_single_measurement()
            if measurement:
                logger.info(f"Single measurement: {measurement}")
            
            # Test short scan
            scan_data = []
            
            def scan_callback(scan):
                scan_data.append(scan)
                logger.info(f"Scan received: {len(scan.points)} points")
            
            if lidar.start_scan(callback=scan_callback):
                time.sleep(2)  # Collect data for 2 seconds
                lidar.stop_scan()
                
                if scan_data:
                    logger.info(f"Collected {len(scan_data)} scans")
                else:
                    logger.warning("No scan data collected")
            else:
                logger.error("Failed to start scanning")
        else:
            logger.error(f"Failed to connect to LIDAR")
        
        # Cleanup
        lidar.disconnect()
        
    except Exception as e:
        logger.error(f"LIDAR test failed: {e}")


if __name__ == "__main__":
    # Detect available LIDAR devices
    detected_devices = detect_lidar_devices()
    print(f"Detected LIDAR devices: {detected_devices}")
    
    # Test first available device
    if detected_devices:
        device = detected_devices[0]
        lidar_type_map = {
            "rplidar": LidarType.RPLIDAR,
            "ydlidar": LidarType.YDLIDAR,
            "hokuyo_urg": LidarType.HOKUYO_URG,
            "generic_serial": LidarType.GENERIC_SERIAL
        }
        
        test_type = lidar_type_map.get(device.get("likely_type"), LidarType.GENERIC_SERIAL)
        test_lidar(test_type, device["port"])