#!/usr/bin/env python3
"""
Jetson Nano Orin Edge SDK - Main Entry Point
"""

import sys
import signal
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.sdk_manager import SDKManager
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    if hasattr(signal_handler, 'sdk_manager'):
        signal_handler.sdk_manager.shutdown()
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Jetson Nano Orin Edge SDK')
    parser.add_argument('--config', '-c', default='config/config.json',
                       help='Path to configuration file')
    parser.add_argument('--log-level', '-l', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = ConfigLoader.load_config(args.config)
        
        # Setup logging
        logger = setup_logger(config['logging'], args.log_level)
        logger.info("Starting Jetson Nano Orin Edge SDK")
        
        # Initialize and run SDK
        sdk_manager = SDKManager(config)
        signal_handler.sdk_manager = sdk_manager  # Store for signal handler
        
        logger.info("SDK initialized successfully")
        sdk_manager.run()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()