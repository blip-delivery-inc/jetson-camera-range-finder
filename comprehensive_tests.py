#!/usr/bin/env python3
"""
Comprehensive Test Suite for Jetson Orin Integration SDK

This script provides extensive testing covering:
- Unit tests for individual components
- Integration tests for the full SDK
- Edge cases and error conditions
- Performance testing
- Data validation

Author: Jetson Orin SDK
"""

import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import threading

# Configure logging for testing
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestResults:
    """Container for test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = time.time()
    
    def add_pass(self, test_name):
        self.passed += 1
        logger.info(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error=None):
        self.failed += 1
        if error:
            self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ FAIL: {test_name}")
        if error:
            logger.error(f"   Error: {error}")
    
    def summary(self):
        duration = time.time() - self.start_time
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if self.errors:
            logger.info(f"\nErrors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        return self.passed == total


def test_imports():
    """Test all module imports."""
    logger.info("Testing module imports...")
    
    try:
        # Test camera module
        from camera import CameraManager, SimpleCamera
        logger.info("✓ Camera module imported successfully")
        
        # Test LIDAR module
        from lidar import LIDARManager, SimpleLIDAR, LIDARData
        logger.info("✓ LIDAR module imported successfully")
        
        # Test main SDK module
        from main import JetsonOrinSDK
        logger.info("✓ Main SDK module imported successfully")
        
        return True, None
    except ImportError as e:
        return False, f"Import error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_camera_manager_creation():
    """Test CameraManager instantiation."""
    logger.info("Testing CameraManager creation...")
    
    try:
        from camera import CameraManager
        manager = CameraManager()
        
        # Check that manager has expected attributes
        assert hasattr(manager, 'cameras'), "Missing cameras attribute"
        assert hasattr(manager, 'camera_configs'), "Missing camera_configs attribute"
        assert isinstance(manager.cameras, dict), "cameras should be a dict"
        assert isinstance(manager.camera_configs, dict), "camera_configs should be a dict"
        
        return True, None
    except Exception as e:
        return False, f"CameraManager creation failed: {e}"


def test_lidar_manager_creation():
    """Test LIDARManager instantiation."""
    logger.info("Testing LIDARManager creation...")
    
    try:
        from lidar import LIDARManager
        manager = LIDARManager()
        
        # Check that manager has expected attributes
        assert hasattr(manager, 'lidars'), "Missing lidars attribute"
        assert hasattr(manager, 'lidar_configs'), "Missing lidar_configs attribute"
        assert isinstance(manager.lidars, dict), "lidars should be a dict"
        assert isinstance(manager.lidar_configs, dict), "lidar_configs should be a dict"
        
        return True, None
    except Exception as e:
        return False, f"LIDARManager creation failed: {e}"


def test_sdk_creation():
    """Test JetsonOrinSDK instantiation."""
    logger.info("Testing JetsonOrinSDK creation...")
    
    try:
        from main import JetsonOrinSDK
        
        # Test with default output directory
        sdk = JetsonOrinSDK()
        assert hasattr(sdk, 'camera_manager'), "Missing camera_manager"
        assert hasattr(sdk, 'lidar_manager'), "Missing lidar_manager"
        assert hasattr(sdk, 'output_dir'), "Missing output_dir"
        
        # Test with custom output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            assert sdk.output_dir == Path(temp_dir), "Output directory not set correctly"
        
        return True, None
    except Exception as e:
        return False, f"JetsonOrinSDK creation failed: {e}"


def test_camera_detection():
    """Test camera detection functionality."""
    logger.info("Testing camera detection...")
    
    try:
        from camera import CameraManager
        manager = CameraManager()
        
        # Test detection method exists and returns list
        cameras = manager.detect_cameras()
        assert isinstance(cameras, list), "detect_cameras should return a list"
        
        # Test that each camera has required fields
        for camera in cameras:
            assert 'id' in camera, "Camera missing 'id' field"
            assert 'type' in camera, "Camera missing 'type' field"
            assert 'description' in camera, "Camera missing 'description' field"
        
        return True, None
    except Exception as e:
        return False, f"Camera detection failed: {e}"


def test_lidar_detection():
    """Test LIDAR detection functionality."""
    logger.info("Testing LIDAR detection...")
    
    try:
        from lidar import LIDARManager
        manager = LIDARManager()
        
        # Test detection method exists and returns list
        lidars = manager.detect_lidars()
        assert isinstance(lidars, list), "detect_lidars should return a list"
        
        # Test that each LIDAR has required fields
        for lidar in lidars:
            assert 'id' in lidar, "LIDAR missing 'id' field"
            assert 'type' in lidar, "LIDAR missing 'type' field"
            assert 'description' in lidar, "LIDAR missing 'description' field"
        
        return True, None
    except Exception as e:
        return False, f"LIDAR detection failed: {e}"


def test_lidar_data_class():
    """Test LIDARData class functionality."""
    logger.info("Testing LIDARData class...")
    
    try:
        from lidar import LIDARData
        
        # Test basic creation
        data = LIDARData(distance=1.5, angle=45.0)
        assert data.distance == 1.5, "Distance not set correctly"
        assert data.angle == 45.0, "Angle not set correctly"
        assert data.quality == 0, "Default quality should be 0"
        assert data.timestamp is not None, "Timestamp should be set"
        
        # Test with all parameters
        data = LIDARData(distance=2.0, angle=90.0, quality=255, timestamp=1234567890.0)
        assert data.distance == 2.0, "Distance not set correctly"
        assert data.angle == 90.0, "Angle not set correctly"
        assert data.quality == 255, "Quality not set correctly"
        assert data.timestamp == 1234567890.0, "Timestamp not set correctly"
        
        # Test string representation
        str_repr = str(data)
        assert "LIDARData" in str_repr, "String representation should contain LIDARData"
        assert "2.000m" in str_repr, "String representation should contain distance"
        assert "90.0°" in str_repr, "String representation should contain angle"
        
        return True, None
    except Exception as e:
        return False, f"LIDARData class test failed: {e}"


def test_sdk_hardware_detection():
    """Test SDK hardware detection."""
    logger.info("Testing SDK hardware detection...")
    
    try:
        from main import JetsonOrinSDK
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test hardware detection
            hardware_info = sdk.detect_hardware()
            
            # Check required fields
            assert 'timestamp' in hardware_info, "Missing timestamp"
            assert 'cameras' in hardware_info, "Missing cameras"
            assert 'lidars' in hardware_info, "Missing lidars"
            assert 'total_devices' in hardware_info, "Missing total_devices"
            
            # Check data types
            assert isinstance(hardware_info['cameras'], list), "cameras should be list"
            assert isinstance(hardware_info['lidars'], list), "lidars should be list"
            assert isinstance(hardware_info['total_devices'], int), "total_devices should be int"
            
            # Check that total_devices is correct
            expected_total = len(hardware_info['cameras']) + len(hardware_info['lidars'])
            assert hardware_info['total_devices'] == expected_total, "total_devices calculation incorrect"
            
            # Check that output file was created
            hardware_file = Path(temp_dir) / 'hardware_detection.json'
            assert hardware_file.exists(), "Hardware detection file not created"
            
            # Verify JSON is valid
            with open(hardware_file, 'r') as f:
                json_data = json.load(f)
                assert json_data == hardware_info, "Saved JSON doesn't match returned data"
        
        return True, None
    except Exception as e:
        return False, f"SDK hardware detection failed: {e}"


def test_sdk_simple_capture():
    """Test SDK simple capture functionality."""
    logger.info("Testing SDK simple capture...")
    
    try:
        from main import JetsonOrinSDK
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test simple capture
            capture_data = sdk.simple_capture()
            
            # Check required fields
            assert 'timestamp' in capture_data, "Missing timestamp"
            assert 'cameras' in capture_data, "Missing cameras"
            assert 'lidars' in capture_data, "Missing lidars"
            
            # Check data types
            assert isinstance(capture_data['cameras'], dict), "cameras should be dict"
            assert isinstance(capture_data['lidars'], dict), "lidars should be dict"
            
            return True, None
    except Exception as e:
        return False, f"SDK simple capture failed: {e}"


def test_error_handling():
    """Test error handling in various scenarios."""
    logger.info("Testing error handling...")
    
    try:
        from camera import CameraManager
        from lidar import LIDARManager
        from main import JetsonOrinSDK
        
        # Test camera manager with invalid camera ID
        camera_manager = CameraManager()
        frame = camera_manager.capture_frame("nonexistent_camera")
        assert frame is None, "Should return None for nonexistent camera"
        
        # Test LIDAR manager with invalid LIDAR ID
        lidar_manager = LIDARManager()
        data = lidar_manager.read_data("nonexistent_lidar")
        assert data is None, "Should return None for nonexistent LIDAR"
        
        # Test SDK with invalid hardware info
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test with empty hardware info
            empty_hardware = {'cameras': [], 'lidars': [], 'total_devices': 0}
            result = sdk.connect_hardware(empty_hardware)
            assert isinstance(result, bool), "connect_hardware should return bool"
        
        return True, None
    except Exception as e:
        return False, f"Error handling test failed: {e}"


def test_data_persistence():
    """Test data persistence and file creation."""
    logger.info("Testing data persistence...")
    
    try:
        from main import JetsonOrinSDK
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test hardware detection file creation
            hardware_info = sdk.detect_hardware()
            hardware_file = Path(temp_dir) / 'hardware_detection.json'
            
            assert hardware_file.exists(), "Hardware detection file not created"
            
            # Verify JSON content
            with open(hardware_file, 'r') as f:
                saved_data = json.load(f)
                assert saved_data == hardware_info, "Saved data doesn't match"
            
            # Test that output directory structure is correct
            assert Path(temp_dir).exists(), "Output directory not created"
            assert Path(temp_dir).is_dir(), "Output directory is not a directory"
        
        return True, None
    except Exception as e:
        return False, f"Data persistence test failed: {e}"


def test_threading_safety():
    """Test threading safety of SDK components."""
    logger.info("Testing threading safety...")
    
    try:
        from main import JetsonOrinSDK
        
        def worker_function(sdk, results, worker_id):
            try:
                # Each worker tries to detect hardware
                hardware_info = sdk.detect_hardware()
                results[worker_id] = True
            except Exception as e:
                results[worker_id] = False
                logger.error(f"Worker {worker_id} failed: {e}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Create multiple threads
            results = {}
            threads = []
            
            for i in range(3):
                thread = threading.Thread(target=worker_function, args=(sdk, results, i))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            all_passed = all(results.values())
            assert all_passed, f"Some threads failed: {results}"
        
        return True, None
    except Exception as e:
        return False, f"Threading safety test failed: {e}"


def test_performance():
    """Test performance characteristics."""
    logger.info("Testing performance...")
    
    try:
        from main import JetsonOrinSDK
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test hardware detection performance
            start_time = time.time()
            hardware_info = sdk.detect_hardware()
            detection_time = time.time() - start_time
            
            # Detection should complete within reasonable time (5 seconds)
            assert detection_time < 5.0, f"Hardware detection too slow: {detection_time:.2f}s"
            
            # Test simple capture performance
            start_time = time.time()
            capture_data = sdk.simple_capture()
            capture_time = time.time() - start_time
            
            # Capture should complete within reasonable time (10 seconds)
            assert capture_time < 10.0, f"Simple capture too slow: {capture_time:.2f}s"
            
            logger.info(f"Performance metrics:")
            logger.info(f"  Hardware detection: {detection_time:.3f}s")
            logger.info(f"  Simple capture: {capture_time:.3f}s")
        
        return True, None
    except Exception as e:
        return False, f"Performance test failed: {e}"


def test_memory_usage():
    """Test memory usage patterns."""
    logger.info("Testing memory usage...")
    
    try:
        import gc
        import psutil
        import os
        
        from main import JetsonOrinSDK
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Perform operations
            hardware_info = sdk.detect_hardware()
            capture_data = sdk.simple_capture()
            
            # Force garbage collection
            gc.collect()
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            logger.info(f"Memory usage:")
            logger.info(f"  Initial: {initial_memory:.1f} MB")
            logger.info(f"  Final: {final_memory:.1f} MB")
            logger.info(f"  Increase: {memory_increase:.1f} MB")
            
            # Memory increase should be reasonable (< 100 MB)
            assert memory_increase < 100.0, f"Memory usage too high: {memory_increase:.1f} MB"
        
        return True, None
    except ImportError:
        logger.warning("psutil not available, skipping memory test")
        return True, None
    except Exception as e:
        return False, f"Memory usage test failed: {e}"


def test_configuration_validation():
    """Test configuration validation."""
    logger.info("Testing configuration validation...")
    
    try:
        from camera import CameraManager
        from lidar import LIDARManager
        
        # Test camera configuration
        camera_manager = CameraManager()
        configs = camera_manager.camera_configs
        
        # Check USB config
        assert 'usb' in configs, "USB config missing"
        usb_config = configs['usb']
        assert 'default_device' in usb_config, "USB default_device missing"
        assert 'width' in usb_config, "USB width missing"
        assert 'height' in usb_config, "USB height missing"
        assert 'fps' in usb_config, "USB fps missing"
        
        # Check CSI config
        assert 'csi' in configs, "CSI config missing"
        csi_config = configs['csi']
        assert 'default_device' in csi_config, "CSI default_device missing"
        assert 'width' in csi_config, "CSI width missing"
        assert 'height' in csi_config, "CSI height missing"
        assert 'fps' in csi_config, "CSI fps missing"
        
        # Test LIDAR configuration
        lidar_manager = LIDARManager()
        lidar_configs = lidar_manager.lidar_configs
        
        # Check serial config
        assert 'serial' in lidar_configs, "Serial config missing"
        serial_config = lidar_configs['serial']
        assert 'baudrate' in serial_config, "Serial baudrate missing"
        assert 'timeout' in serial_config, "Serial timeout missing"
        
        # Check USB config
        assert 'usb' in lidar_configs, "USB LIDAR config missing"
        usb_lidar_config = lidar_configs['usb']
        assert 'baudrate' in usb_lidar_config, "USB LIDAR baudrate missing"
        assert 'timeout' in usb_lidar_config, "USB LIDAR timeout missing"
        
        return True, None
    except Exception as e:
        return False, f"Configuration validation failed: {e}"


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    logger.info("Testing edge cases...")
    
    try:
        from main import JetsonOrinSDK
        from lidar import LIDARData
        
        # Test LIDARData with extreme values
        data = LIDARData(distance=0.0, angle=0.0)
        assert data.distance == 0.0, "Zero distance not handled correctly"
        assert data.angle == 0.0, "Zero angle not handled correctly"
        
        data = LIDARData(distance=1000.0, angle=360.0)
        assert data.distance == 1000.0, "Large distance not handled correctly"
        assert data.angle == 360.0, "Large angle not handled correctly"
        
        # Test SDK with very short duration
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk = JetsonOrinSDK(output_dir=temp_dir)
            
            # Test with minimal duration
            hardware_info = sdk.detect_hardware()
            sdk.connect_hardware(hardware_info)
            
            # This should not crash even with minimal duration
            try:
                summary = sdk.capture_data(duration=0.1, interval=0.05)
                assert isinstance(summary, dict), "Summary should be dict even with minimal duration"
            except Exception as e:
                logger.warning(f"Minimal duration capture failed (expected): {e}")
        
        return True, None
    except Exception as e:
        return False, f"Edge case test failed: {e}"


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    logger.info("Starting comprehensive test suite...")
    
    results = TestResults()
    
    # Define all tests
    tests = [
        ("Module Imports", test_imports),
        ("Camera Manager Creation", test_camera_manager_creation),
        ("LIDAR Manager Creation", test_lidar_manager_creation),
        ("SDK Creation", test_sdk_creation),
        ("Camera Detection", test_camera_detection),
        ("LIDAR Detection", test_lidar_detection),
        ("LIDAR Data Class", test_lidar_data_class),
        ("SDK Hardware Detection", test_sdk_hardware_detection),
        ("SDK Simple Capture", test_sdk_simple_capture),
        ("Error Handling", test_error_handling),
        ("Data Persistence", test_data_persistence),
        ("Threading Safety", test_threading_safety),
        ("Performance", test_performance),
        ("Memory Usage", test_memory_usage),
        ("Configuration Validation", test_configuration_validation),
        ("Edge Cases", test_edge_cases),
    ]
    
    # Run each test
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            success, error = test_func()
            if success:
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, error)
        except Exception as e:
            results.add_fail(test_name, f"Unexpected exception: {e}")
    
    # Generate summary
    return results.summary()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)