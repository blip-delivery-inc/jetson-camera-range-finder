"""
Configuration Loader - Handles loading and validating configuration files
"""

import json
import os
from typing import Dict, Any
import logging


class ConfigLoader:
    """Configuration loader with validation"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        logger = logging.getLogger(__name__)
        
        try:
            # Check if file exists
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            # Load JSON configuration
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate configuration
            ConfigLoader._validate_config(config)
            
            logger.info(f"Configuration loaded successfully from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]):
        """Validate configuration structure"""
        required_sections = ['system', 'cameras', 'laser', 'processing', 'output', 'logging']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate camera configuration
        if config['cameras']['enabled']:
            if 'devices' not in config['cameras']:
                raise ValueError("Camera devices configuration missing")
            
            for device in config['cameras']['devices']:
                required_camera_fields = ['id', 'name', 'type', 'device_id', 'width', 'height', 'fps']
                for field in required_camera_fields:
                    if field not in device:
                        raise ValueError(f"Missing required camera field: {field}")
        
        # Validate laser configuration
        if config['laser']['enabled']:
            if 'device' not in config['laser']:
                raise ValueError("Laser device configuration missing")
            
            required_laser_fields = ['id', 'name', 'type', 'port', 'baudrate']
            for field in required_laser_fields:
                if field not in config['laser']['device']:
                    raise ValueError(f"Missing required laser field: {field}")
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """Save configuration to JSON file"""
        logger = logging.getLogger(__name__)
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Configuration saved successfully to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration template"""
        return {
            "system": {
                "name": "Jetson Nano Orin Edge SDK",
                "version": "1.0.0",
                "log_level": "INFO",
                "data_dir": "./data"
            },
            "cameras": {
                "enabled": True,
                "devices": [
                    {
                        "id": "camera_0",
                        "name": "Front Camera",
                        "type": "usb",
                        "device_id": 0,
                        "width": 640,
                        "height": 480,
                        "fps": 30,
                        "format": "BGR",
                        "enabled": True
                    }
                ]
            },
            "laser": {
                "enabled": True,
                "device": {
                    "id": "laser_0",
                    "name": "Laser Range Finder",
                    "type": "uart",
                    "port": "/dev/ttyUSB0",
                    "baudrate": 115200,
                    "timeout": 1.0,
                    "protocol": "standard"
                },
                "processing": {
                    "filter_outliers": True,
                    "moving_average_window": 5,
                    "min_distance": 0.1,
                    "max_distance": 10.0
                }
            },
            "processing": {
                "image": {
                    "resize": True,
                    "target_width": 640,
                    "target_height": 480,
                    "apply_filters": False,
                    "save_frames": False
                },
                "fusion": {
                    "enabled": True,
                    "sync_tolerance_ms": 100,
                    "output_format": "json"
                }
            },
            "output": {
                "api": {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 8080,
                    "cors_enabled": True
                },
                "websocket": {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 8081
                },
                "storage": {
                    "enabled": True,
                    "max_files": 1000,
                    "max_file_size_mb": 10,
                    "compression": True
                }
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/edge_sdk.log",
                "max_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }