"""
Data Fusion Engine - Combines camera and laser data for unified processing
"""

import threading
import time
import json
from typing import Dict, Any, Optional, List
from collections import deque
import logging
import cv2
import numpy as np

from utils.logger import LoggerMixin


class FusionEngine(LoggerMixin):
    """Fuses camera and laser data for enhanced perception"""
    
    def __init__(self, config: Dict[str, Any], camera_manager=None, laser_manager=None):
        self.config = config
        self.camera_manager = camera_manager
        self.laser_manager = laser_manager
        
        # Fusion settings
        self.sync_tolerance_ms = config.get('sync_tolerance_ms', 100)
        self.output_format = config.get('output_format', 'json')
        
        # Fusion state
        self.running = False
        self.latest_fused_data = None
        self.fusion_count = 0
        
        # Data buffers
        self.camera_buffer = deque(maxlen=10)
        self.laser_buffer = deque(maxlen=10)
        
        # Threading
        self.lock = threading.Lock()
        self.thread = None
        
        self.logger.info("Fusion engine initialized")
    
    def start(self):
        """Start fusion processing"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._fusion_loop, name="FusionEngine")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("Fusion engine started")
    
    def stop(self):
        """Stop fusion processing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Fusion engine stopped")
    
    def _fusion_loop(self):
        """Main fusion processing loop"""
        while self.running:
            try:
                # Get latest data from sensors
                camera_data = self._get_latest_camera_data()
                laser_data = self._get_latest_laser_data()
                
                # Perform data fusion
                if camera_data and laser_data:
                    fused_data = self._fuse_data(camera_data, laser_data)
                    
                    if fused_data:
                        with self.lock:
                            self.latest_fused_data = fused_data
                            self.fusion_count += 1
                
                # Processing rate (10Hz)
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in fusion loop: {e}")
                time.sleep(1.0)
    
    def _get_latest_camera_data(self) -> Optional[Dict[str, Any]]:
        """Get latest camera data from all cameras"""
        if not self.camera_manager:
            return None
        
        try:
            all_frames = self.camera_manager.get_all_frames()
            
            if all_frames:
                # Store in buffer with timestamp
                camera_data = {
                    'frames': all_frames,
                    'timestamp': time.time(),
                    'camera_count': len(all_frames)
                }
                
                self.camera_buffer.append(camera_data)
                return camera_data
            
        except Exception as e:
            self.logger.error(f"Error getting camera data: {e}")
        
        return None
    
    def _get_latest_laser_data(self) -> Optional[Dict[str, Any]]:
        """Get latest laser data"""
        if not self.laser_manager:
            return None
        
        try:
            laser_data = self.laser_manager.get_distance()
            
            if laser_data:
                # Store in buffer with timestamp
                self.laser_buffer.append(laser_data)
                return laser_data
            
        except Exception as e:
            self.logger.error(f"Error getting laser data: {e}")
        
        return None
    
    def _fuse_data(self, camera_data: Dict[str, Any], laser_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fuse camera and laser data"""
        try:
            # Check temporal synchronization
            time_diff = abs(camera_data['timestamp'] - laser_data['timestamp'])
            
            if time_diff > (self.sync_tolerance_ms / 1000.0):
                self.logger.debug(f"Data not synchronized: {time_diff*1000:.1f}ms difference")
                return None
            
            # Create fused data structure
            fused_data = {
                'timestamp': time.time(),
                'fusion_id': self.fusion_count,
                'synchronized': True,
                'time_diff_ms': time_diff * 1000,
                
                # Camera data
                'cameras': {
                    camera_id: {
                        'frame_info': {
                            'timestamp': frame_data['timestamp'],
                            'frame_count': frame_data['frame_count'],
                            'fps': frame_data['fps'],
                            'camera_id': frame_data['camera_id'],
                            'camera_name': frame_data['camera_name']
                        },
                        'frame_shape': frame_data['frame'].shape,
                        'frame_size_bytes': frame_data['frame'].nbytes
                    }
                    for camera_id, frame_data in camera_data['frames'].items()
                },
                
                # Laser data
                'laser': {
                    'distance': laser_data['distance'],
                    'timestamp': laser_data['timestamp'],
                    'reading_count': laser_data['reading_count'],
                    'error_count': laser_data['error_count'],
                    'device_id': laser_data['device_id'],
                    'device_name': laser_data['device_name']
                },
                
                # Fusion metadata
                'metadata': {
                    'camera_count': camera_data['camera_count'],
                    'laser_connected': laser_data['connected'],
                    'fusion_quality': self._calculate_fusion_quality(camera_data, laser_data)
                }
            }
            
            # Add processed data if requested
            if self.output_format == 'json':
                fused_data['processed'] = self._process_fused_data(camera_data, laser_data)
            
            return fused_data
            
        except Exception as e:
            self.logger.error(f"Error fusing data: {e}")
            return None
    
    def _calculate_fusion_quality(self, camera_data: Dict[str, Any], laser_data: Dict[str, Any]) -> float:
        """Calculate fusion quality score (0-1)"""
        quality = 1.0
        
        # Check camera quality
        if camera_data['camera_count'] == 0:
            quality *= 0.5
        
        # Check laser quality
        if laser_data['error_count'] > 0:
            error_rate = laser_data['error_count'] / max(laser_data['reading_count'], 1)
            quality *= (1.0 - error_rate)
        
        # Check temporal synchronization
        time_diff = abs(camera_data['timestamp'] - laser_data['timestamp'])
        sync_quality = max(0, 1.0 - (time_diff * 10))  # Penalize time differences
        quality *= sync_quality
        
        return max(0.0, min(1.0, quality))
    
    def _process_fused_data(self, camera_data: Dict[str, Any], laser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process fused data for analysis"""
        processed = {
            'distance_analysis': self._analyze_distance(laser_data),
            'camera_analysis': self._analyze_cameras(camera_data),
            'combined_analysis': self._analyze_combined(camera_data, laser_data)
        }
        
        return processed
    
    def _analyze_distance(self, laser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze laser distance data"""
        distance = laser_data['distance']
        
        analysis = {
            'current_distance': distance,
            'distance_category': self._categorize_distance(distance),
            'safety_level': self._calculate_safety_level(distance),
            'trend': 'stable'  # Could be enhanced with historical analysis
        }
        
        return analysis
    
    def _analyze_cameras(self, camera_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze camera data"""
        analysis = {
            'active_cameras': camera_data['camera_count'],
            'total_fps': sum(frame['fps'] for frame in camera_data['frames'].values()),
            'frame_quality': 'good'  # Could be enhanced with image quality metrics
        }
        
        return analysis
    
    def _analyze_combined(self, camera_data: Dict[str, Any], laser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze combined sensor data"""
        distance = laser_data['distance']
        
        analysis = {
            'environment_assessment': self._assess_environment(distance),
            'sensor_agreement': True,  # Could be enhanced with cross-validation
            'confidence_score': 0.85  # Could be enhanced with uncertainty quantification
        }
        
        return analysis
    
    def _categorize_distance(self, distance: float) -> str:
        """Categorize distance into ranges"""
        if distance < 0.5:
            return 'very_close'
        elif distance < 1.0:
            return 'close'
        elif distance < 3.0:
            return 'medium'
        elif distance < 5.0:
            return 'far'
        else:
            return 'very_far'
    
    def _calculate_safety_level(self, distance: float) -> str:
        """Calculate safety level based on distance"""
        if distance < 0.3:
            return 'critical'
        elif distance < 0.8:
            return 'warning'
        elif distance < 2.0:
            return 'caution'
        else:
            return 'safe'
    
    def _assess_environment(self, distance: float) -> str:
        """Assess environment based on sensor data"""
        if distance < 0.5:
            return 'obstacle_detected'
        elif distance < 1.5:
            return 'narrow_space'
        else:
            return 'open_space'
    
    def get_fused_data(self) -> Optional[Dict[str, Any]]:
        """Get latest fused data"""
        with self.lock:
            if self.latest_fused_data:
                return self.latest_fused_data.copy()
        return None
    
    def get_fusion_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get fusion history"""
        # This could be enhanced to store historical fused data
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get fusion engine status"""
        return {
            'running': self.running,
            'fusion_count': self.fusion_count,
            'camera_buffer_size': len(self.camera_buffer),
            'laser_buffer_size': len(self.laser_buffer),
            'sync_tolerance_ms': self.sync_tolerance_ms,
            'output_format': self.output_format,
            'latest_fusion_available': self.latest_fused_data is not None
        }
    
    def shutdown(self):
        """Shutdown fusion engine"""
        self.stop()
        self.logger.info("Fusion engine shutdown complete")