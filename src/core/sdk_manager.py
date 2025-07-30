"""
SDK Manager - Main coordinator for all edge SDK components
"""

import threading
import time
from typing import Dict, Any
import logging

from drivers.camera_manager import CameraManager
from drivers.laser_manager import LaserManager
from processing.fusion_engine import FusionEngine
from output.api_server import APIServer
from output.websocket_server import WebSocketServer
from output.storage_manager import StorageManager


class SDKManager:
    """Main SDK manager that coordinates all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Component managers
        self.camera_manager = None
        self.laser_manager = None
        self.fusion_engine = None
        self.api_server = None
        self.websocket_server = None
        self.storage_manager = None
        
        # Threading
        self.running = False
        self.threads = []
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all SDK components"""
        try:
            # Initialize storage manager first
            if self.config['output']['storage']['enabled']:
                self.storage_manager = StorageManager(self.config['output']['storage'])
                self.logger.info("Storage manager initialized")
            
            # Initialize camera manager
            if self.config['cameras']['enabled']:
                self.camera_manager = CameraManager(self.config['cameras'])
                self.logger.info("Camera manager initialized")
            
            # Initialize laser manager
            if self.config['laser']['enabled']:
                self.laser_manager = LaserManager(self.config['laser'])
                self.logger.info("Laser manager initialized")
            
            # Initialize fusion engine
            if self.config['processing']['fusion']['enabled']:
                self.fusion_engine = FusionEngine(
                    self.config['processing']['fusion'],
                    self.camera_manager,
                    self.laser_manager
                )
                self.logger.info("Fusion engine initialized")
            
            # Initialize output servers
            if self.config['output']['api']['enabled']:
                self.api_server = APIServer(
                    self.config['output']['api'],
                    self.camera_manager,
                    self.laser_manager,
                    self.fusion_engine
                )
                self.logger.info("API server initialized")
            
            if self.config['output']['websocket']['enabled']:
                self.websocket_server = WebSocketServer(
                    self.config['output']['websocket'],
                    self.camera_manager,
                    self.laser_manager,
                    self.fusion_engine
                )
                self.logger.info("WebSocket server initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def run(self):
        """Start all SDK components"""
        self.running = True
        self.logger.info("Starting SDK components...")
        
        try:
            # Start camera manager
            if self.camera_manager:
                camera_thread = threading.Thread(
                    target=self.camera_manager.start,
                    name="CameraManager"
                )
                camera_thread.daemon = True
                camera_thread.start()
                self.threads.append(camera_thread)
            
            # Start laser manager
            if self.laser_manager:
                laser_thread = threading.Thread(
                    target=self.laser_manager.start,
                    name="LaserManager"
                )
                laser_thread.daemon = True
                laser_thread.start()
                self.threads.append(laser_thread)
            
            # Start fusion engine
            if self.fusion_engine:
                fusion_thread = threading.Thread(
                    target=self.fusion_engine.start,
                    name="FusionEngine"
                )
                fusion_thread.daemon = True
                fusion_thread.start()
                self.threads.append(fusion_thread)
            
            # Start API server
            if self.api_server:
                api_thread = threading.Thread(
                    target=self.api_server.start,
                    name="APIServer"
                )
                api_thread.daemon = True
                api_thread.start()
                self.threads.append(api_thread)
            
            # Start WebSocket server
            if self.websocket_server:
                ws_thread = threading.Thread(
                    target=self.websocket_server.start,
                    name="WebSocketServer"
                )
                ws_thread.daemon = True
                ws_thread.start()
                self.threads.append(ws_thread)
            
            self.logger.info("All components started successfully")
            
            # Main loop
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown all SDK components gracefully"""
        self.logger.info("Shutting down SDK components...")
        self.running = False
        
        # Shutdown components in reverse order
        if self.websocket_server:
            self.websocket_server.shutdown()
        
        if self.api_server:
            self.api_server.shutdown()
        
        if self.fusion_engine:
            self.fusion_engine.shutdown()
        
        if self.laser_manager:
            self.laser_manager.shutdown()
        
        if self.camera_manager:
            self.camera_manager.shutdown()
        
        if self.storage_manager:
            self.storage_manager.shutdown()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("SDK shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current SDK status"""
        status = {
            'running': self.running,
            'components': {}
        }
        
        if self.camera_manager:
            status['components']['camera'] = self.camera_manager.get_status()
        
        if self.laser_manager:
            status['components']['laser'] = self.laser_manager.get_status()
        
        if self.fusion_engine:
            status['components']['fusion'] = self.fusion_engine.get_status()
        
        if self.api_server:
            status['components']['api'] = self.api_server.get_status()
        
        if self.websocket_server:
            status['components']['websocket'] = self.websocket_server.get_status()
        
        return status