"""
Configuration management for Jetson Edge SDK
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CameraConfig:
    """Camera configuration settings"""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    format: str = "MJPG"  # or "YUYV"
    device_id: int = 0
    flip_method: int = 0  # For CSI cameras: 0=none, 1=ccw90, 2=180, 3=cw90
    capture_width: int = 1920
    capture_height: int = 1080


@dataclass 
class RangeFinderConfig:
    """Range finder configuration settings"""
    port: str = "/dev/ttyUSB0"
    baudrate: int = 115200
    timeout: float = 1.0
    max_range: float = 100.0  # meters
    min_range: float = 0.1    # meters
    scan_angle: float = 270.0  # degrees


@dataclass
class SDKConfig:
    """Main SDK configuration"""
    camera: CameraConfig
    range_finder: RangeFinderConfig
    data_output_dir: str = "./data"
    log_level: str = "INFO"
    enable_camera: bool = True
    enable_range_finder: bool = True
    

class Config:
    """Configuration manager for the SDK"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self._config = self._load_default_config()
        
        if os.path.exists(self.config_path):
            self.load_from_file(self.config_path)
    
    def _load_default_config(self) -> SDKConfig:
        """Load default configuration"""
        return SDKConfig(
            camera=CameraConfig(),
            range_finder=RangeFinderConfig()
        )
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            # Update configuration with loaded values
            if 'camera' in config_dict:
                for key, value in config_dict['camera'].items():
                    if hasattr(self._config.camera, key):
                        setattr(self._config.camera, key, value)
            
            if 'range_finder' in config_dict:
                for key, value in config_dict['range_finder'].items():
                    if hasattr(self._config.range_finder, key):
                        setattr(self._config.range_finder, key, value)
            
            # Update main config
            for key, value in config_dict.items():
                if key not in ['camera', 'range_finder'] and hasattr(self._config, key):
                    setattr(self._config, key, value)
                    
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to JSON file"""
        path = config_path or self.config_path
        config_dict = asdict(self._config)
        
        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @property
    def camera(self) -> CameraConfig:
        return self._config.camera
    
    @property 
    def range_finder(self) -> RangeFinderConfig:
        return self._config.range_finder
    
    @property
    def data_output_dir(self) -> str:
        return self._config.data_output_dir
    
    @property
    def log_level(self) -> str:
        return self._config.log_level
    
    @property
    def enable_camera(self) -> bool:
        return self._config.enable_camera
    
    @property
    def enable_range_finder(self) -> bool:
        return self._config.enable_range_finder