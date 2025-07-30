"""
Jetson Edge SDK - A simple SDK for camera and laser range finder operations on Jetson Nano Orin
"""

__version__ = "1.0.0"
__author__ = "Jetson Edge SDK Team"

from .core.sdk import JetsonEdgeSDK
from .core.camera import CameraManager
from .core.range_finder import RangeFinderManager
from .core.config import Config

__all__ = [
    'JetsonEdgeSDK',
    'CameraManager', 
    'RangeFinderManager',
    'Config'
]