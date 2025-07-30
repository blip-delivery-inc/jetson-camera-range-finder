"""
Laser Range Finder Manager - Handles laser distance sensor communication
"""

import serial
import threading
import time
import re
from typing import Dict, Any, Optional, List
from collections import deque
import logging
import statistics

from utils.logger import LoggerMixin


class LaserRangeFinder(LoggerMixin):
    """Laser range finder device interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device_config = config['device']
        self.processing_config = config['processing']
        
        # Device properties
        self.id = self.device_config['id']
        self.name = self.device_config['name']
        self.port = self.device_config['port']
        self.baudrate = self.device_config['baudrate']
        self.timeout = self.device_config.get('timeout', 1.0)
        self.protocol = self.device_config.get('protocol', 'standard')
        
        # Processing settings
        self.filter_outliers = self.processing_config.get('filter_outliers', True)
        self.moving_average_window = self.processing_config.get('moving_average_window', 5)
        self.min_distance = self.processing_config.get('min_distance', 0.1)
        self.max_distance = self.processing_config.get('max_distance', 10.0)
        
        # Device state
        self.serial_conn = None
        self.running = False
        self.connected = False
        
        # Data storage
        self.latest_distance = None
        self.latest_timestamp = None
        self.distance_history = deque(maxlen=100)
        self.reading_count = 0
        self.error_count = 0
        
        # Threading
        self.lock = threading.Lock()
        self.thread = None
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize serial connection to laser range finder"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Test connection
            if self.serial_conn.is_open:
                self.connected = True
                self.logger.info(f"Connected to laser range finder on {self.port}")
                
                # Send initialization command if needed
                self._send_init_command()
            else:
                raise RuntimeError("Failed to open serial connection")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize laser connection: {e}")
            self.connected = False
            raise
    
    def _send_init_command(self):
        """Send initialization command to laser range finder"""
        try:
            # Common initialization commands for laser range finders
            init_commands = [
                b'\x00',  # Null command
                b'V',     # Version command
                b'D',     # Distance command
            ]
            
            for cmd in init_commands:
                self.serial_conn.write(cmd)
                time.sleep(0.1)
                
            self.logger.info("Initialization commands sent")
            
        except Exception as e:
            self.logger.warning(f"Failed to send init commands: {e}")
    
    def start(self):
        """Start laser reading thread"""
        if not self.connected or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._reading_loop, name=f"Laser_{self.id}")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("Laser reading started")
    
    def stop(self):
        """Stop laser reading"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        self.connected = False
        self.logger.info("Laser reading stopped")
    
    def _reading_loop(self):
        """Main reading loop"""
        while self.running:
            try:
                distance = self._read_distance()
                
                if distance is not None:
                    with self.lock:
                        self.latest_distance = distance
                        self.latest_timestamp = time.time()
                        self.distance_history.append(distance)
                        self.reading_count += 1
                
                # Reading rate (typically 10Hz for laser range finders)
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in reading loop: {e}")
                self.error_count += 1
                time.sleep(1.0)
    
    def _read_distance(self) -> Optional[float]:
        """Read distance from laser range finder"""
        try:
            if not self.serial_conn.is_open:
                return None
            
            # Clear input buffer
            self.serial_conn.reset_input_buffer()
            
            # Send distance request command
            self.serial_conn.write(b'D')
            
            # Read response
            response = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
            
            if response:
                distance = self._parse_distance(response)
                
                if distance is not None:
                    # Apply filters
                    if self.filter_outliers:
                        distance = self._filter_outlier(distance)
                    
                    # Apply distance limits
                    if self.min_distance <= distance <= self.max_distance:
                        return distance
                    else:
                        self.logger.debug(f"Distance {distance}m outside valid range")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading distance: {e}")
            return None
    
    def _parse_distance(self, response: str) -> Optional[float]:
        """Parse distance from response string"""
        try:
            # Common patterns for laser range finder responses
            patterns = [
                r'(\d+\.?\d*)',  # Simple number
                r'D:(\d+\.?\d*)',  # Distance prefix
                r'Distance:(\d+\.?\d*)',  # Distance label
                r'(\d+\.?\d*)m',  # With meter unit
                r'(\d+\.?\d*)mm',  # Millimeters
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response)
                if match:
                    value = float(match.group(1))
                    
                    # Convert mm to meters if needed
                    if 'mm' in response:
                        value /= 1000.0
                    
                    return value
            
            self.logger.debug(f"Could not parse distance from response: {response}")
            return None
            
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to parse distance value: {e}")
            return None
    
    def _filter_outlier(self, distance: float) -> float:
        """Filter outliers using statistical methods"""
        if len(self.distance_history) < 3:
            return distance
        
        # Calculate moving average
        recent_distances = list(self.distance_history)[-self.moving_average_window:]
        mean_distance = statistics.mean(recent_distances)
        
        # Check if current reading is an outlier (more than 2 standard deviations)
        if len(recent_distances) >= 3:
            std_dev = statistics.stdev(recent_distances)
            if abs(distance - mean_distance) > 2 * std_dev:
                self.logger.debug(f"Filtered outlier: {distance}m (mean: {mean_distance:.3f}m)")
                return mean_distance
        
        return distance
    
    def get_distance(self) -> Optional[Dict[str, Any]]:
        """Get latest distance reading with metadata"""
        with self.lock:
            if self.latest_distance is not None:
                return {
                    'distance': self.latest_distance,
                    'timestamp': self.latest_timestamp,
                    'reading_count': self.reading_count,
                    'error_count': self.error_count,
                    'connected': self.connected,
                    'device_id': self.id,
                    'device_name': self.name
                }
        return None
    
    def get_distance_history(self, count: int = 10) -> List[float]:
        """Get recent distance history"""
        with self.lock:
            return list(self.distance_history)[-count:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get laser device status"""
        return {
            'id': self.id,
            'name': self.name,
            'connected': self.connected,
            'running': self.running,
            'reading_count': self.reading_count,
            'error_count': self.error_count,
            'latest_distance': self.latest_distance,
            'port': self.port,
            'baudrate': self.baudrate
        }


class LaserManager(LoggerMixin):
    """Manages laser range finder devices"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.laser = None
        self.running = False
        
        # Initialize laser
        self._initialize_laser()
    
    def _initialize_laser(self):
        """Initialize laser range finder"""
        try:
            self.laser = LaserRangeFinder(self.config)
            self.logger.info("Laser range finder initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize laser: {e}")
            self.laser = None
    
    def start(self):
        """Start laser reading"""
        if self.laser:
            self.running = True
            self.laser.start()
            self.logger.info("Laser manager started")
    
    def stop(self):
        """Stop laser reading"""
        self.running = False
        if self.laser:
            self.laser.stop()
        self.logger.info("Laser manager stopped")
    
    def get_distance(self) -> Optional[Dict[str, Any]]:
        """Get latest distance reading"""
        if self.laser:
            return self.laser.get_distance()
        return None
    
    def get_distance_history(self, count: int = 10) -> List[float]:
        """Get distance history"""
        if self.laser:
            return self.laser.get_distance_history(count)
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get laser manager status"""
        status = {
            'running': self.running,
            'laser_available': self.laser is not None
        }
        
        if self.laser:
            status['laser'] = self.laser.get_status()
        
        return status
    
    def shutdown(self):
        """Shutdown laser manager"""
        self.stop()
        self.logger.info("Laser manager shutdown complete")