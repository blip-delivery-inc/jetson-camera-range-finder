#!/usr/bin/env python3
"""
Test script for Jetson Edge SDK
Tests the SDK structure and basic functionality without requiring hardware
"""

import sys
import os
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all SDK modules can be imported"""
    print("Testing SDK imports...")
    
    try:
        # Test core module imports
        from jetson_edge_sdk.core.config import Config, CameraConfig, RangeFinderConfig
        print("✓ Config classes imported successfully")
        
        from jetson_edge_sdk.core.camera import CameraManager
        print("✓ CameraManager imported successfully")
        
        from jetson_edge_sdk.core.range_finder import RangeFinderManager, RangeReading, ScanData
        print("✓ RangeFinderManager and data classes imported successfully")
        
        from jetson_edge_sdk.core.sdk import JetsonEdgeSDK
        print("✓ JetsonEdgeSDK imported successfully")
        
        # Test main package import
        from jetson_edge_sdk import JetsonEdgeSDK as MainSDK
        print("✓ Main package import successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration management"""
    print("\nTesting configuration management...")
    
    try:
        from jetson_edge_sdk.core.config import Config
        
        # Test default config creation
        config = Config()
        print("✓ Default config created")
        
        # Test config properties
        assert hasattr(config, 'camera')
        assert hasattr(config, 'range_finder')
        assert hasattr(config, 'enable_camera')
        assert hasattr(config, 'enable_range_finder')
        print("✓ Config properties accessible")
        
        # Test camera config
        assert config.camera.width == 1920
        assert config.camera.height == 1080
        assert config.camera.fps == 30
        print("✓ Camera config values correct")
        
        # Test range finder config
        assert config.range_finder.port == "/dev/ttyUSB0"
        assert config.range_finder.baudrate == 115200
        print("✓ Range finder config values correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        traceback.print_exc()
        return False

def test_sdk_creation():
    """Test SDK object creation"""
    print("\nTesting SDK object creation...")
    
    try:
        from jetson_edge_sdk import JetsonEdgeSDK
        
        # Test SDK creation
        sdk = JetsonEdgeSDK()
        print("✓ SDK object created")
        
        # Test SDK properties
        assert hasattr(sdk, 'config')
        assert hasattr(sdk, 'camera')
        assert hasattr(sdk, 'range_finder')
        assert hasattr(sdk, 'is_initialized')
        assert hasattr(sdk, 'is_running')
        print("✓ SDK properties exist")
        
        # Test initial state
        assert sdk.is_initialized == False
        assert sdk.is_running == False
        print("✓ SDK initial state correct")
        
        # Test methods exist
        assert callable(getattr(sdk, 'initialize'))
        assert callable(getattr(sdk, 'start'))
        assert callable(getattr(sdk, 'stop'))
        assert callable(getattr(sdk, 'release'))
        print("✓ SDK methods exist and are callable")
        
        # Test context manager
        with JetsonEdgeSDK() as context_sdk:
            assert context_sdk is not None
        print("✓ Context manager works")
        
        return True
        
    except Exception as e:
        print(f"✗ SDK creation test failed: {e}")
        traceback.print_exc()
        return False

def test_data_structures():
    """Test data structure classes"""
    print("\nTesting data structures...")
    
    try:
        from jetson_edge_sdk.core.range_finder import RangeReading, ScanData
        import time
        
        # Test RangeReading
        reading = RangeReading(
            angle=45.0,
            distance=2.5,
            quality=200,
            timestamp=time.time()
        )
        assert reading.angle == 45.0
        assert reading.distance == 2.5
        print("✓ RangeReading structure works")
        
        # Test ScanData
        readings = [reading]
        scan = ScanData(
            readings=readings,
            scan_time=0.1,
            timestamp=time.time()
        )
        assert len(scan.readings) == 1
        assert scan.scan_time == 0.1
        print("✓ ScanData structure works")
        
        return True
        
    except Exception as e:
        print(f"✗ Data structure test failed: {e}")
        traceback.print_exc()
        return False

def test_examples_syntax():
    """Test that example files have valid syntax"""
    print("\nTesting example files syntax...")
    
    example_files = [
        'examples/basic_usage.py',
        'examples/advanced_callbacks.py',
        'examples/obstacle_detection.py'
    ]
    
    for example_file in example_files:
        try:
            with open(example_file, 'r') as f:
                code = f.read()
            
            # Compile to check syntax
            compile(code, example_file, 'exec')
            print(f"✓ {example_file} syntax is valid")
            
        except Exception as e:
            print(f"✗ {example_file} syntax error: {e}")
            return False
    
    return True

def test_config_file():
    """Test configuration file"""
    print("\nTesting configuration file...")
    
    try:
        import json
        
        with open('config.json', 'r') as f:
            config_data = json.load(f)
        
        # Check required sections
        required_sections = ['camera', 'range_finder']
        for section in required_sections:
            assert section in config_data, f"Missing section: {section}"
        
        # Check camera config
        camera_config = config_data['camera']
        required_camera_fields = ['width', 'height', 'fps', 'device_id']
        for field in required_camera_fields:
            assert field in camera_config, f"Missing camera field: {field}"
        
        # Check range finder config
        rf_config = config_data['range_finder']
        required_rf_fields = ['port', 'baudrate', 'timeout']
        for field in required_rf_fields:
            assert field in rf_config, f"Missing range finder field: {field}"
        
        print("✓ Configuration file structure is valid")
        return True
        
    except Exception as e:
        print(f"✗ Config file test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("JETSON EDGE SDK TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_config),
        ("SDK Creation Tests", test_sdk_creation),
        ("Data Structure Tests", test_data_structures),
        ("Example Syntax Tests", test_examples_syntax),
        ("Config File Tests", test_config_file),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! SDK is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)