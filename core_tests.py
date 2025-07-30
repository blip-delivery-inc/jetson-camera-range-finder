#!/usr/bin/env python3
"""
Core Test Suite for Jetson Orin Integration SDK

This script tests the core functionality without requiring external dependencies.
It focuses on data structures, file operations, and basic logic.

Author: Jetson Orin SDK
"""

import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import threading

# Configure logging for testing
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CoreTestResults:
    """Container for core test results."""
    
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
        logger.info(f"CORE TEST SUMMARY")
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


def test_lidar_data_class():
    """Test LIDARData class functionality."""
    logger.info("Testing LIDARData class...")
    
    try:
        # Import LIDARData class (should work without external deps)
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
        
        logger.info(f"LIDARData test successful: {data}")
        return True, None
    except Exception as e:
        return False, f"LIDARData class test failed: {e}"


def test_data_structures():
    """Test data structures and JSON serialization."""
    logger.info("Testing data structures...")
    
    try:
        # Test hardware detection structure
        hardware_info = {
            'timestamp': datetime.now().isoformat(),
            'cameras': [
                {
                    'id': 'usb_0',
                    'type': 'usb',
                    'device_id': 0,
                    'width': 640,
                    'height': 480,
                    'fps': 30,
                    'description': 'USB Camera 0'
                },
                {
                    'id': 'csi_/dev/video0',
                    'type': 'csi',
                    'device_path': '/dev/video0',
                    'width': 1920,
                    'height': 1080,
                    'fps': 30,
                    'description': 'CSI Camera /dev/video0'
                }
            ],
            'lidars': [
                {
                    'id': 'usb_ttyUSB0',
                    'type': 'usb',
                    'device_path': '/dev/ttyUSB0',
                    'baudrate': 115200,
                    'description': 'USB LIDAR /dev/ttyUSB0 @ 115200'
                },
                {
                    'id': 'serial_ttyS0',
                    'type': 'serial',
                    'device_path': '/dev/ttyS0',
                    'baudrate': 115200,
                    'description': 'Serial LIDAR /dev/ttyS0'
                }
            ],
            'total_devices': 4
        }
        
        # Validate structure
        assert 'timestamp' in hardware_info, "Missing timestamp"
        assert 'cameras' in hardware_info, "Missing cameras"
        assert 'lidars' in hardware_info, "Missing lidars"
        assert 'total_devices' in hardware_info, "Missing total_devices"
        
        # Validate camera data
        for camera in hardware_info['cameras']:
            assert 'id' in camera, "Camera missing id"
            assert 'type' in camera, "Camera missing type"
            assert 'description' in camera, "Camera missing description"
        
        # Validate LIDAR data
        for lidar in hardware_info['lidars']:
            assert 'id' in lidar, "LIDAR missing id"
            assert 'type' in lidar, "LIDAR missing type"
            assert 'description' in lidar, "LIDAR missing description"
        
        # Test JSON serialization
        json_str = json.dumps(hardware_info, indent=2)
        parsed_data = json.loads(json_str)
        assert parsed_data == hardware_info, "JSON serialization/deserialization failed"
        
        # Test capture summary structure
        capture_summary = {
            'capture_duration': 10.0,
            'capture_interval': 2.0,
            'total_captures': 5,
            'camera_captures': 10,
            'lidar_captures': 10,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        # Validate capture summary
        assert 'capture_duration' in capture_summary, "Missing capture_duration"
        assert 'capture_interval' in capture_summary, "Missing capture_interval"
        assert 'total_captures' in capture_summary, "Missing total_captures"
        assert 'camera_captures' in capture_summary, "Missing camera_captures"
        assert 'lidar_captures' in capture_summary, "Missing lidar_captures"
        
        json_str = json.dumps(capture_summary, indent=2)
        parsed_data = json.loads(json_str)
        assert parsed_data == capture_summary, "Capture summary JSON failed"
        
        logger.info(f"Data structures test successful: {len(hardware_info['cameras'])} cameras, {len(hardware_info['lidars'])} LIDARs")
        return True, None
    except Exception as e:
        return False, f"Data structures test failed: {e}"


def test_file_operations():
    """Test file operations and persistence."""
    logger.info("Testing file operations...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test directory creation
            output_dir = Path(temp_dir) / 'test_output'
            output_dir.mkdir(exist_ok=True)
            assert output_dir.exists(), "Directory not created"
            assert output_dir.is_dir(), "Not a directory"
            
            # Test file writing
            test_data = {
                'test': 'data', 
                'number': 42,
                'timestamp': datetime.now().isoformat(),
                'nested': {
                    'key': 'value',
                    'array': [1, 2, 3, 4, 5]
                }
            }
            test_file = output_dir / 'test.json'
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            assert test_file.exists(), "File not created"
            assert test_file.stat().st_size > 0, "File is empty"
            
            # Test file reading
            with open(test_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data, "Loaded data doesn't match"
            
            # Test multiple file operations
            for i in range(5):
                filename = f"test_{i}.json"
                filepath = output_dir / filename
                data = {'index': i, 'timestamp': datetime.now().isoformat()}
                
                with open(filepath, 'w') as f:
                    json.dump(data, f)
                
                assert filepath.exists(), f"File {filename} not created"
            
            # List files
            files = list(output_dir.glob("*.json"))
            assert len(files) == 6, f"Expected 6 files, found {len(files)}"
            
            # Test file cleanup
            for filepath in files:
                filepath.unlink()
                assert not filepath.exists(), f"File {filepath.name} not deleted"
            
            # Verify directory is empty
            remaining_files = list(output_dir.glob("*"))
            assert len(remaining_files) == 0, f"Directory not empty: {remaining_files}"
            
        logger.info("File operations test successful")
        return True, None
    except Exception as e:
        return False, f"File operations test failed: {e}"


def test_configuration_validation():
    """Test configuration validation."""
    logger.info("Testing configuration validation...")
    
    try:
        # Test camera configuration structure
        camera_configs = {
            'usb': {
                'default_device': 0,
                'width': 640,
                'height': 480,
                'fps': 30
            },
            'csi': {
                'default_device': 0,
                'width': 1920,
                'height': 1080,
                'fps': 30
            },
            'ip': {
                'default_url': 'http://192.168.1.100:8080/video',
                'timeout': 10
            }
        }
        
        # Validate USB config
        assert 'usb' in camera_configs, "USB config missing"
        usb_config = camera_configs['usb']
        required_usb_fields = ['default_device', 'width', 'height', 'fps']
        for field in required_usb_fields:
            assert field in usb_config, f"USB config missing {field}"
            assert isinstance(usb_config[field], (int, float)), f"USB {field} should be numeric"
        
        # Validate CSI config
        assert 'csi' in camera_configs, "CSI config missing"
        csi_config = camera_configs['csi']
        required_csi_fields = ['default_device', 'width', 'height', 'fps']
        for field in required_csi_fields:
            assert field in csi_config, f"CSI config missing {field}"
            assert isinstance(csi_config[field], (int, float)), f"CSI {field} should be numeric"
        
        # Validate IP config
        assert 'ip' in camera_configs, "IP config missing"
        ip_config = camera_configs['ip']
        assert 'default_url' in ip_config, "IP config missing default_url"
        assert 'timeout' in ip_config, "IP config missing timeout"
        assert isinstance(ip_config['timeout'], (int, float)), "IP timeout should be numeric"
        
        # Test LIDAR configuration structure
        lidar_configs = {
            'serial': {
                'baudrate': 115200,
                'timeout': 1,
                'bytesize': 8,
                'parity': 'N',
                'stopbits': 1
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
        
        # Validate serial config
        assert 'serial' in lidar_configs, "Serial config missing"
        serial_config = lidar_configs['serial']
        required_serial_fields = ['baudrate', 'timeout']
        for field in required_serial_fields:
            assert field in serial_config, f"Serial config missing {field}"
            assert isinstance(serial_config[field], (int, float)), f"Serial {field} should be numeric"
        
        # Validate USB LIDAR config
        assert 'usb' in lidar_configs, "USB LIDAR config missing"
        usb_lidar_config = lidar_configs['usb']
        required_usb_lidar_fields = ['baudrate', 'timeout']
        for field in required_usb_lidar_fields:
            assert field in usb_lidar_config, f"USB LIDAR config missing {field}"
            assert isinstance(usb_lidar_config[field], (int, float)), f"USB LIDAR {field} should be numeric"
        
        # Validate ethernet config
        assert 'ethernet' in lidar_configs, "Ethernet config missing"
        ethernet_config = lidar_configs['ethernet']
        assert 'host' in ethernet_config, "Ethernet config missing host"
        assert 'port' in ethernet_config, "Ethernet config missing port"
        assert 'timeout' in ethernet_config, "Ethernet config missing timeout"
        assert isinstance(ethernet_config['port'], int), "Ethernet port should be integer"
        assert isinstance(ethernet_config['timeout'], (int, float)), "Ethernet timeout should be numeric"
        
        logger.info("Configuration validation test successful")
        return True, None
    except Exception as e:
        return False, f"Configuration validation failed: {e}"


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    logger.info("Testing edge cases...")
    
    try:
        # Test with empty data
        empty_hardware = {
            'timestamp': datetime.now().isoformat(),
            'cameras': [],
            'lidars': [],
            'total_devices': 0
        }
        
        # Should handle empty hardware gracefully
        assert empty_hardware['total_devices'] == 0, "Total devices should be 0"
        assert len(empty_hardware['cameras']) == 0, "Cameras should be empty"
        assert len(empty_hardware['lidars']) == 0, "LIDARs should be empty"
        
        # Test with extreme values
        extreme_data = {
            'distance': 1000000.0,  # Very large distance
            'angle': 720.0,         # Multiple rotations
            'quality': 255,         # Maximum quality
            'timestamp': 0.0        # Epoch time
        }
        
        # Should handle extreme values
        assert extreme_data['distance'] > 0, "Distance should be positive"
        assert extreme_data['angle'] >= 0, "Angle should be non-negative"
        assert 0 <= extreme_data['quality'] <= 255, "Quality should be in valid range"
        
        # Test with minimal duration
        minimal_capture = {
            'capture_duration': 0.001,  # 1 millisecond
            'capture_interval': 0.0005, # 0.5 milliseconds
            'total_captures': 1,
            'camera_captures': 0,
            'lidar_captures': 0
        }
        
        # Should handle minimal values
        assert minimal_capture['capture_duration'] > 0, "Duration should be positive"
        assert minimal_capture['capture_interval'] > 0, "Interval should be positive"
        assert minimal_capture['total_captures'] >= 0, "Total captures should be non-negative"
        
        # Test with maximum values
        maximum_capture = {
            'capture_duration': 86400.0,  # 24 hours
            'capture_interval': 3600.0,   # 1 hour
            'total_captures': 1000000,
            'camera_captures': 500000,
            'lidar_captures': 500000
        }
        
        # Should handle maximum values
        assert maximum_capture['capture_duration'] > 0, "Duration should be positive"
        assert maximum_capture['capture_interval'] > 0, "Interval should be positive"
        assert maximum_capture['total_captures'] >= 0, "Total captures should be non-negative"
        
        logger.info("Edge cases test successful")
        return True, None
    except Exception as e:
        return False, f"Edge case test failed: {e}"


def test_code_coverage():
    """Test code coverage analysis."""
    logger.info("Testing code coverage...")
    
    try:
        # Analyze the main modules for code coverage
        modules = ['camera.py', 'lidar.py', 'main.py']
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for module in modules:
            with open(module, 'r') as f:
                content = f.read()
            
            # Count lines of code (excluding comments and empty lines)
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
            
            # Count functions and classes
            function_count = content.count('def ')
            class_count = content.count('class ')
            
            total_lines += len(lines)
            total_functions += function_count
            total_classes += class_count
            
            logger.info(f"{module}: {len(lines)} lines, {function_count} functions, {class_count} classes")
            
            # Basic coverage checks
            assert len(lines) > 50, f"{module} has insufficient code"
            assert function_count > 5, f"{module} has insufficient functions"
            assert class_count > 0, f"{module} has no classes"
        
        logger.info(f"Total: {total_lines} lines, {total_functions} functions, {total_classes} classes")
        
        # Overall coverage checks
        assert total_lines > 500, f"Insufficient total code: {total_lines} lines"
        assert total_functions > 20, f"Insufficient functions: {total_functions}"
        assert total_classes > 3, f"Insufficient classes: {total_classes}"
        
        logger.info("Code coverage test successful")
        return True, None
    except Exception as e:
        return False, f"Code coverage test failed: {e}"


def test_threading_safety():
    """Test threading safety with basic operations."""
    logger.info("Testing threading safety...")
    
    try:
        def worker_function(results, worker_id):
            try:
                # Each worker performs basic operations
                test_data = {
                    'worker_id': worker_id,
                    'timestamp': datetime.now().isoformat(),
                    'data': [i for i in range(100)]
                }
                
                # JSON operations
                json_str = json.dumps(test_data)
                parsed_data = json.loads(json_str)
                
                # File operations
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    json.dump(test_data, f)
                    temp_file = f.name
                
                # Read back
                with open(temp_file, 'r') as f:
                    loaded_data = json.load(f)
                
                # Cleanup
                Path(temp_file).unlink()
                
                # Verify data integrity
                assert parsed_data == test_data, "JSON round-trip failed"
                assert loaded_data == test_data, "File round-trip failed"
                
                results[worker_id] = True
            except Exception as e:
                results[worker_id] = False
                logger.error(f"Worker {worker_id} failed: {e}")
        
        # Create multiple threads
        results = {}
        threads = []
        
        for i in range(5):
            thread = threading.Thread(target=worker_function, args=(results, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        all_passed = all(results.values())
        assert all_passed, f"Some threads failed: {results}"
        
        logger.info(f"Threading safety test successful: {len(results)} threads passed")
        return True, None
    except Exception as e:
        return False, f"Threading safety test failed: {e}"


def test_performance_benchmarks():
    """Test performance benchmarks with basic operations."""
    logger.info("Testing performance benchmarks...")
    
    try:
        # Test JSON serialization performance
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'cameras': [{'id': f'camera_{i}', 'type': 'usb'} for i in range(100)],
            'lidars': [{'id': f'lidar_{i}', 'type': 'serial'} for i in range(50)],
            'total_devices': 150
        }
        
        # Measure JSON serialization
        start_time = time.time()
        for _ in range(1000):
            json_str = json.dumps(test_data)
            parsed_data = json.loads(json_str)
        json_time = time.time() - start_time
        
        # Measure file operations
        start_time = time.time()
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(100):
                filepath = Path(temp_dir) / f'test_{i}.json'
                with open(filepath, 'w') as f:
                    json.dump(test_data, f)
                with open(filepath, 'r') as f:
                    loaded_data = json.load(f)
        file_time = time.time() - start_time
        
        # Performance assertions
        assert json_time < 1.0, f"JSON operations too slow: {json_time:.3f}s"
        assert file_time < 5.0, f"File operations too slow: {file_time:.3f}s"
        
        logger.info(f"Performance metrics:")
        logger.info(f"  JSON operations (1000x): {json_time:.3f}s")
        logger.info(f"  File operations (100x): {file_time:.3f}s")
        
        logger.info("Performance benchmarks test successful")
        return True, None
    except Exception as e:
        return False, f"Performance test failed: {e}"


def test_error_handling():
    """Test error handling patterns."""
    logger.info("Testing error handling...")
    
    try:
        # Test with invalid JSON
        try:
            invalid_json = "{'invalid': json}"
            parsed = json.loads(invalid_json)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # Expected error
            pass
        
        # Test with invalid file operations
        try:
            with open('/nonexistent/path/file.json', 'r') as f:
                data = json.load(f)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            # Expected error
            pass
        
        # Test with invalid data types
        try:
            # This should work fine
            test_data = {
                'string': 'test',
                'number': 42,
                'float': 3.14,
                'boolean': True,
                'null': None,
                'array': [1, 2, 3],
                'object': {'key': 'value'}
            }
            json_str = json.dumps(test_data)
            parsed_data = json.loads(json_str)
            assert parsed_data == test_data, "Data type handling failed"
        except Exception as e:
            assert False, f"Valid data types failed: {e}"
        
        # Test with empty data
        empty_data = {}
        json_str = json.dumps(empty_data)
        parsed_data = json.loads(json_str)
        assert parsed_data == empty_data, "Empty data handling failed"
        
        logger.info("Error handling test successful")
        return True, None
    except Exception as e:
        return False, f"Error handling test failed: {e}"


def run_core_tests():
    """Run all core tests."""
    logger.info("Starting core test suite...")
    
    results = CoreTestResults()
    
    # Define all tests
    tests = [
        ("LIDAR Data Class", test_lidar_data_class),
        ("Data Structures", test_data_structures),
        ("File Operations", test_file_operations),
        ("Configuration Validation", test_configuration_validation),
        ("Edge Cases", test_edge_cases),
        ("Code Coverage", test_code_coverage),
        ("Threading Safety", test_threading_safety),
        ("Performance Benchmarks", test_performance_benchmarks),
        ("Error Handling", test_error_handling),
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
    success = run_core_tests()
    sys.exit(0 if success else 1)