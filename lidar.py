#!/usr/bin/env python3
"""
Jetson Orin LIDAR Integration Module

This module provides easy-to-use interfaces for reading range data from
connected LIDAR devices (USB, Serial, Ethernet) on the Jetson Orin platform.

Author: Jetson Orin SDK
"""

import serial
import socket
import time
import logging
import struct
import threading
from typing import Optional, List, Dict, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LIDARData:
    """Container for LIDAR measurement data."""
    
    def __init__(self, distance: float, angle: float, quality: int = 0, timestamp: float = None):
        """
        Initialize LIDAR data point.
        
        Args:
            distance: Distance measurement in meters
            angle: Angle measurement in degrees
            quality: Quality indicator (0-255)
            timestamp: Timestamp of measurement
        """
        self.distance = distance
        self.angle = angle
        self.quality = quality
        self.timestamp = timestamp or time.time()
    
    def __str__(self):
        return f"LIDARData(distance={self.distance:.3f}m, angle={self.angle:.1f}°, quality={self.quality})"


class LIDARManager:
    """Manages LIDAR connections and provides unified interface for different LIDAR types."""
    
    def __init__(self):
        self.lidars = {}
        self.lidar_configs = {
            'serial': {
                'baudrate': 115200,
                'timeout': 1,
                'bytesize': serial.EIGHTBITS,
                'parity': serial.PARITY_NONE,
                'stopbits': serial.STOPBITS_ONE
            },
            'usb': {
                'baudrate': 115200,
                'timeout': 1
            },
            'ethernet': {
                'host': '192.168.1.100',
                'port': 2111,
                'timeout': 5
            }
        }
    
    def detect_lidars(self) -> List[dict]:
        """
        Detect available LIDAR devices on the system.
        
        Returns:
            List of detected LIDAR information
        """
        detected_lidars = []
        
        # Check USB LIDARs (common USB-to-Serial devices)
        usb_devices = [
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2'
        ]
        
        for device in usb_devices:
            if Path(device).exists():
                try:
                    # Try to connect with common LIDAR baudrates
                    for baudrate in [115200, 9600, 230400]:
                        try:
                            ser = serial.Serial(device, baudrate, timeout=1)
                            if ser.is_open:
                                # Try to read some data to verify it's a LIDAR
                                ser.write(b'\x55\xAA')  # Common LIDAR start command
                                time.sleep(0.1)
                                if ser.in_waiting > 0:
                                    detected_lidars.append({
                                        'id': f'usb_{device}',
                                        'type': 'usb',
                                        'device_path': device,
                                        'baudrate': baudrate,
                                        'description': f'USB LIDAR {device} @ {baudrate}'
                                    })
                                    logger.info(f"Detected USB LIDAR {device} @ {baudrate} baud")
                                ser.close()
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Error checking device {device}: {str(e)}")
        
        # Check Serial LIDARs
        serial_devices = ['/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2']
        for device in serial_devices:
            if Path(device).exists():
                detected_lidars.append({
                    'id': f'serial_{device}',
                    'type': 'serial',
                    'device_path': device,
                    'baudrate': 115200,
                    'description': f'Serial LIDAR {device}'
                })
                logger.info(f"Detected Serial LIDAR {device}")
        
        return detected_lidars
    
    def connect_lidar(self, lidar_id: str, lidar_info: dict) -> bool:
        """
        Connect to a specific LIDAR device.
        
        Args:
            lidar_id: Unique identifier for the LIDAR
            lidar_info: LIDAR configuration information
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if lidar_info['type'] in ['usb', 'serial']:
                ser = serial.Serial(
                    port=lidar_info['device_path'],
                    baudrate=lidar_info.get('baudrate', 115200),
                    timeout=lidar_info.get('timeout', 1),
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                if ser.is_open:
                    self.lidars[lidar_id] = {
                        'connection': ser,
                        'type': 'serial',
                        'info': lidar_info
                    }
                    logger.info(f"Successfully connected to LIDAR: {lidar_id}")
                    return True
                else:
                    logger.error(f"Failed to open LIDAR: {lidar_id}")
                    return False
                    
            elif lidar_info['type'] == 'ethernet':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(lidar_info.get('timeout', 5))
                sock.connect((lidar_info['host'], lidar_info['port']))
                
                self.lidars[lidar_id] = {
                    'connection': sock,
                    'type': 'ethernet',
                    'info': lidar_info
                }
                logger.info(f"Successfully connected to Ethernet LIDAR: {lidar_id}")
                return True
                
            else:
                logger.error(f"Unsupported LIDAR type: {lidar_info['type']}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to LIDAR {lidar_id}: {str(e)}")
            return False
    
    def read_data(self, lidar_id: str) -> Optional[LIDARData]:
        """
        Read a single data point from the LIDAR.
        
        Args:
            lidar_id: LIDAR identifier
            
        Returns:
            LIDARData object, or None if failed
        """
        if lidar_id not in self.lidars:
            logger.error(f"LIDAR {lidar_id} not connected")
            return None
        
        try:
            lidar = self.lidars[lidar_id]
            
            if lidar['type'] == 'serial':
                return self._read_serial_data(lidar)
            elif lidar['type'] == 'ethernet':
                return self._read_ethernet_data(lidar)
            else:
                logger.error(f"Unknown LIDAR type: {lidar['type']}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading data from LIDAR {lidar_id}: {str(e)}")
            return None
    
    def _read_serial_data(self, lidar: dict) -> Optional[LIDARData]:
        """Read data from serial LIDAR connection."""
        try:
            ser = lidar['connection']
            
            # Read available data
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                
                # Simple parsing for common LIDAR formats
                # This is a basic implementation - specific LIDAR models may need custom parsing
                if len(data) >= 4:
                    # Try to parse as distance data (common format: 2 bytes distance, 2 bytes angle)
                    try:
                        distance_bytes = data[:2]
                        angle_bytes = data[2:4]
                        
                        distance = struct.unpack('<H', distance_bytes)[0] / 1000.0  # Convert to meters
                        angle = struct.unpack('<H', angle_bytes)[0] / 10.0  # Convert to degrees
                        
                        return LIDARData(distance, angle)
                    except:
                        # If parsing fails, return raw data as distance
                        distance = len(data) / 1000.0  # Simple fallback
                        return LIDARData(distance, 0.0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading serial data: {str(e)}")
            return None
    
    def _read_ethernet_data(self, lidar: dict) -> Optional[LIDARData]:
        """Read data from ethernet LIDAR connection."""
        try:
            sock = lidar['connection']
            
            # Send request for data
            sock.send(b'GET_DATA\n')
            
            # Read response
            data = sock.recv(1024)
            
            if data:
                # Parse ethernet data (format depends on LIDAR model)
                try:
                    # Simple parsing - adjust based on actual LIDAR protocol
                    parts = data.decode().strip().split(',')
                    if len(parts) >= 2:
                        distance = float(parts[0])
                        angle = float(parts[1])
                        return LIDARData(distance, angle)
                except:
                    # Fallback parsing
                    distance = len(data) / 1000.0
                    return LIDARData(distance, 0.0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading ethernet data: {str(e)}")
            return None
    
    def get_lidar_info(self, lidar_id: str) -> Optional[dict]:
        """
        Get information about a connected LIDAR.
        
        Args:
            lidar_id: LIDAR identifier
            
        Returns:
            LIDAR information dictionary, or None if not found
        """
        if lidar_id in self.lidars:
            return self.lidars[lidar_id]['info']
        return None
    
    def disconnect_lidar(self, lidar_id: str):
        """
        Disconnect from a LIDAR.
        
        Args:
            lidar_id: LIDAR identifier
        """
        if lidar_id in self.lidars:
            lidar = self.lidars[lidar_id]
            
            if lidar['type'] == 'serial':
                lidar['connection'].close()
            elif lidar['type'] == 'ethernet':
                lidar['connection'].close()
            
            del self.lidars[lidar_id]
            logger.info(f"Disconnected LIDAR: {lidar_id}")
    
    def disconnect_all(self):
        """Disconnect from all LIDARs."""
        for lidar_id in list(self.lidars.keys()):
            self.disconnect_lidar(lidar_id)


class SimpleLIDAR:
    """Simplified LIDAR interface for basic usage."""
    
    def __init__(self, device_path: str = '/dev/ttyUSB0', baudrate: int = 115200):
        """
        Initialize LIDAR with device path and baudrate.
        
        Args:
            device_path: Path to LIDAR device
            baudrate: Communication baudrate
        """
        self.device_path = device_path
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to the LIDAR.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(self.device_path).exists():
                logger.error(f"LIDAR device not found: {self.device_path}")
                return False
            
            self.ser = serial.Serial(
                port=self.device_path,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            if self.ser.is_open:
                self.connected = True
                logger.info(f"Connected to LIDAR device {self.device_path}")
                return True
            else:
                logger.error(f"Failed to open LIDAR device {self.device_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to LIDAR: {str(e)}")
            return False
    
    def read_distance(self) -> Optional[float]:
        """
        Read distance measurement from LIDAR.
        
        Returns:
            Distance in meters, or None if failed
        """
        if not self.connected or self.ser is None:
            logger.error("LIDAR not connected")
            return None
        
        try:
            # Send start command (common for many LIDARs)
            self.ser.write(b'\x55\xAA')
            time.sleep(0.1)
            
            # Read available data
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                
                # Simple distance parsing (adjust based on actual LIDAR protocol)
                if len(data) >= 2:
                    try:
                        distance = struct.unpack('<H', data[:2])[0] / 1000.0
                        return distance
                    except:
                        # Fallback: use data length as distance indicator
                        return len(data) / 1000.0
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading distance: {str(e)}")
            return None
    
    def read_data(self) -> Optional[LIDARData]:
        """
        Read complete LIDAR data.
        
        Returns:
            LIDARData object, or None if failed
        """
        distance = self.read_distance()
        if distance is not None:
            return LIDARData(distance, 0.0)  # Default angle to 0
        return None
    
    def disconnect(self):
        """Disconnect from the LIDAR."""
        if self.ser is not None:
            self.ser.close()
            self.ser = None
            self.connected = False
            logger.info("LIDAR disconnected")


def test_lidar():
    """Test function for LIDAR functionality."""
    logger.info("Testing LIDAR functionality...")
    
    # Test simple LIDAR
    lidar = SimpleLIDAR()
    if lidar.connect():
        distance = lidar.read_distance()
        if distance is not None:
            logger.info(f"Read distance: {distance:.3f} meters")
        else:
            logger.info("No distance data available (this is normal if no LIDAR is connected)")
        lidar.disconnect()
    
    # Test LIDAR manager
    manager = LIDARManager()
    detected = manager.detect_lidars()
    logger.info(f"Detected {len(detected)} LIDAR devices")
    
    for lidar_info in detected:
        if manager.connect_lidar(lidar_info['id'], lidar_info):
            data = manager.read_data(lidar_info['id'])
            if data is not None:
                logger.info(f"Read data from {lidar_info['id']}: {data}")
            manager.disconnect_lidar(lidar_info['id'])


if __name__ == "__main__":
    test_lidar()