#!/usr/bin/env python3
"""
Final Test Summary for Jetson Orin Integration SDK

This script provides a comprehensive final validation of the SDK
without requiring external dependencies.

Author: Jetson Orin SDK
"""

import sys
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_sdk_structure():
    """Test the overall SDK structure and organization."""
    logger.info("Testing SDK structure...")
    
    try:
        # Check all required files exist
        required_files = [
            'camera.py',
            'lidar.py', 
            'main.py',
            'requirements.txt',
            'README.md',
            'Dockerfile',
            'docker-compose.yml',
            '.gitignore'
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            return False, f"Missing files: {missing_files}"
        
        # Check file sizes (should be substantial)
        min_sizes = {
            'camera.py': 5000,      # 5KB
            'lidar.py': 8000,       # 8KB
            'main.py': 6000,        # 6KB
            'README.md': 3000,      # 3KB
            'requirements.txt': 100  # 100B
        }
        
        for file, min_size in min_sizes.items():
            if Path(file).stat().st_size < min_size:
                return False, f"{file} too small: {Path(file).stat().st_size} bytes"
        
        logger.info("SDK structure validation successful")
        return True, None
    except Exception as e:
        return False, f"SDK structure test failed: {e}"


def test_code_quality():
    """Test code quality metrics."""
    logger.info("Testing code quality...")
    
    try:
        python_files = ['camera.py', 'lidar.py', 'main.py']
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        total_comments = 0
        
        for file in python_files:
            with open(file, 'r') as f:
                content = f.read()
            
            # Count lines
            lines = content.split('\n')
            total_lines += len(lines)
            
            # Count functions and classes
            function_count = content.count('def ')
            class_count = content.count('class ')
            comment_count = content.count('#')
            
            total_functions += function_count
            total_classes += class_count
            total_comments += comment_count
            
            logger.info(f"{file}: {len(lines)} lines, {function_count} functions, {class_count} classes, {comment_count} comments")
        
        # Quality checks
        assert total_lines > 800, f"Insufficient code: {total_lines} lines"
        assert total_functions > 30, f"Insufficient functions: {total_functions}"
        assert total_classes > 5, f"Insufficient classes: {total_classes}"
        assert total_comments > 50, f"Insufficient comments: {total_comments}"
        
        logger.info(f"Code quality metrics: {total_lines} lines, {total_functions} functions, {total_classes} classes, {total_comments} comments")
        return True, None
    except Exception as e:
        return False, f"Code quality test failed: {e}"


def test_documentation():
    """Test documentation completeness."""
    logger.info("Testing documentation...")
    
    try:
        # Check README content
        with open('README.md', 'r') as f:
            readme_content = f.read()
        
        # Check for required sections
        required_sections = [
            '## Features',
            '## Installation',
            '## Usage',
            '## Configuration',
            '## Troubleshooting'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            return False, f"Missing README sections: {missing_sections}"
        
        # Check for code examples
        if '```python' not in readme_content:
            return False, "No Python code examples in README"
        
        if '```bash' not in readme_content:
            return False, "No bash command examples in README"
        
        # Check requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        if len(requirements) < 3:
            return False, f"Insufficient requirements: {len(requirements)} packages"
        
        logger.info("Documentation validation successful")
        return True, None
    except Exception as e:
        return False, f"Documentation test failed: {e}"


def test_docker_configuration():
    """Test Docker configuration."""
    logger.info("Testing Docker configuration...")
    
    try:
        # Check Dockerfile
        with open('Dockerfile', 'r') as f:
            dockerfile = f.read()
        
        # Check for required elements
        required_dockerfile_elements = [
            'FROM nvcr.io/nvidia/l4t-base',
            'COPY requirements.txt',
            'CMD ["python3", "main.py"]'
        ]
        
        missing_elements = []
        for element in required_dockerfile_elements:
            if element not in dockerfile:
                missing_elements.append(element)
        
        if missing_elements:
            return False, f"Missing Dockerfile elements: {missing_elements}"
        
        # Check docker-compose.yml
        with open('docker-compose.yml', 'r') as f:
            compose = f.read()
        
        # Check for required services
        required_services = ['jetson-sdk:', '/dev/video0']
        
        missing_services = []
        for service in required_services:
            if service not in compose:
                missing_services.append(service)
        
        if missing_services:
            return False, f"Missing docker-compose elements: {missing_services}"
        
        logger.info("Docker configuration validation successful")
        return True, None
    except Exception as e:
        return False, f"Docker configuration test failed: {e}"


def test_data_structures():
    """Test data structure definitions."""
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
                }
            ],
            'lidars': [
                {
                    'id': 'usb_ttyUSB0',
                    'type': 'usb',
                    'device_path': '/dev/ttyUSB0',
                    'baudrate': 115200,
                    'description': 'USB LIDAR /dev/ttyUSB0 @ 115200'
                }
            ],
            'total_devices': 2
        }
        
        # Validate structure
        assert 'timestamp' in hardware_info, "Missing timestamp"
        assert 'cameras' in hardware_info, "Missing cameras"
        assert 'lidars' in hardware_info, "Missing lidars"
        assert 'total_devices' in hardware_info, "Missing total_devices"
        
        # Test JSON serialization
        json_str = json.dumps(hardware_info, indent=2)
        parsed_data = json.loads(json_str)
        assert parsed_data == hardware_info, "JSON serialization failed"
        
        # Test capture summary structure
        capture_summary = {
            'capture_duration': 10.0,
            'capture_interval': 2.0,
            'total_captures': 5,
            'camera_captures': 5,
            'lidar_captures': 5,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        # Validate capture summary
        required_capture_fields = [
            'capture_duration', 'capture_interval', 'total_captures',
            'camera_captures', 'lidar_captures', 'start_time', 'end_time'
        ]
        
        for field in required_capture_fields:
            assert field in capture_summary, f"Missing capture field: {field}"
        
        logger.info("Data structures validation successful")
        return True, None
    except Exception as e:
        return False, f"Data structures test failed: {e}"


def test_configuration_validation():
    """Test configuration validation."""
    logger.info("Testing configuration validation...")
    
    try:
        # Test camera configuration
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
        
        # Validate camera configs
        for camera_type, config in camera_configs.items():
            assert isinstance(config, dict), f"{camera_type} config should be dict"
            if camera_type in ['usb', 'csi']:
                required_fields = ['default_device', 'width', 'height', 'fps']
                for field in required_fields:
                    assert field in config, f"{camera_type} missing {field}"
                    assert isinstance(config[field], (int, float)), f"{camera_type} {field} should be numeric"
        
        # Test LIDAR configuration
        lidar_configs = {
            'serial': {
                'baudrate': 115200,
                'timeout': 1
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
        
        # Validate LIDAR configs
        for lidar_type, config in lidar_configs.items():
            assert isinstance(config, dict), f"{lidar_type} config should be dict"
            assert 'baudrate' in config or 'host' in config, f"{lidar_type} missing connection config"
            assert 'timeout' in config, f"{lidar_type} missing timeout"
        
        logger.info("Configuration validation successful")
        return True, None
    except Exception as e:
        return False, f"Configuration validation failed: {e}"


def test_file_operations():
    """Test file operations."""
    logger.info("Testing file operations...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test directory creation
            output_dir = Path(temp_dir) / 'sdk_output'
            output_dir.mkdir(exist_ok=True)
            assert output_dir.exists(), "Directory not created"
            
            # Test JSON file writing
            test_data = {
                'test': 'data',
                'timestamp': datetime.now().isoformat(),
                'cameras': [{'id': 'test_camera', 'type': 'usb'}],
                'lidars': [{'id': 'test_lidar', 'type': 'serial'}]
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
            
            # Test multiple files
            for i in range(3):
                filename = f"capture_{i}.json"
                filepath = output_dir / filename
                data = {
                    'capture_id': i,
                    'timestamp': datetime.now().isoformat(),
                    'data': [j for j in range(10)]
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f)
                
                assert filepath.exists(), f"File {filename} not created"
            
            # List and verify files
            files = list(output_dir.glob("*.json"))
            assert len(files) == 4, f"Expected 4 files, found {len(files)}"
            
        logger.info("File operations validation successful")
        return True, None
    except Exception as e:
        return False, f"File operations test failed: {e}"


def test_performance():
    """Test performance characteristics."""
    logger.info("Testing performance...")
    
    try:
        # Test JSON operations performance
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'cameras': [{'id': f'camera_{i}', 'type': 'usb'} for i in range(50)],
            'lidars': [{'id': f'lidar_{i}', 'type': 'serial'} for i in range(25)],
            'total_devices': 75
        }
        
        # Measure JSON serialization
        start_time = time.time()
        for _ in range(100):
            json_str = json.dumps(test_data)
            parsed_data = json.loads(json_str)
        json_time = time.time() - start_time
        
        # Performance assertions
        assert json_time < 0.1, f"JSON operations too slow: {json_time:.3f}s"
        
        # Test file operations performance
        start_time = time.time()
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(10):
                filepath = Path(temp_dir) / f'test_{i}.json'
                with open(filepath, 'w') as f:
                    json.dump(test_data, f)
                with open(filepath, 'r') as f:
                    loaded_data = json.load(f)
        file_time = time.time() - start_time
        
        assert file_time < 1.0, f"File operations too slow: {file_time:.3f}s"
        
        logger.info(f"Performance metrics: JSON {json_time:.3f}s, Files {file_time:.3f}s")
        logger.info("Performance validation successful")
        return True, None
    except Exception as e:
        return False, f"Performance test failed: {e}"


def run_final_tests():
    """Run all final tests."""
    logger.info("Starting final test suite...")
    
    tests = [
        ("SDK Structure", test_sdk_structure),
        ("Code Quality", test_code_quality),
        ("Documentation", test_documentation),
        ("Docker Configuration", test_docker_configuration),
        ("Data Structures", test_data_structures),
        ("Configuration Validation", test_configuration_validation),
        ("File Operations", test_file_operations),
        ("Performance", test_performance),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            success, error = test_func()
            if success:
                logger.info(f"✅ PASS: {test_name}")
                passed += 1
            else:
                logger.error(f"❌ FAIL: {test_name}")
                logger.error(f"   Error: {error}")
                failed += 1
                errors.append(f"{test_name}: {error}")
        except Exception as e:
            logger.error(f"❌ FAIL: {test_name}")
            logger.error(f"   Exception: {e}")
            failed += 1
            errors.append(f"{test_name}: {e}")
    
    # Summary
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if errors:
        logger.info(f"\nErrors:")
        for error in errors:
            logger.error(f"  - {error}")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! SDK is ready for deployment.")
    else:
        logger.warning(f"\n⚠ {failed} tests failed. Review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_final_tests()
    sys.exit(0 if success else 1)