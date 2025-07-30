#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Test Suite

This script provides comprehensive testing for the SDK components:
- Hardware detection tests
- Camera functionality tests
- LIDAR functionality tests
- Integration tests
- Error handling tests

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import os
import sys
import time
import json
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, LidarType, detect_lidar_devices, LidarError
from main import JetsonSDK

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestJetsonCamera(unittest.TestCase):
    """Test cases for JetsonCamera class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_output_dir = Path("test_output")
        self.test_output_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up test files
        if self.test_output_dir.exists():
            for file in self.test_output_dir.glob("*"):
                file.unlink()
            self.test_output_dir.rmdir()
    
    def test_camera_initialization(self):
        """Test camera initialization with different parameters"""
        # Test USB camera
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        self.assertEqual(camera.camera_type, "usb")
        self.assertEqual(camera.camera_id, 0)
        
        # Test CSI camera
        camera = JetsonCamera(camera_type="csi", camera_id=1)
        self.assertEqual(camera.camera_type, "csi")
        self.assertEqual(camera.camera_id, 1)
        
        # Test IP camera
        camera = JetsonCamera(camera_type="ip", ip_url="http://192.168.1.100:8080/video")
        self.assertEqual(camera.camera_type, "ip")
        self.assertEqual(camera.ip_url, "http://192.168.1.100:8080/video")
    
    def test_camera_validation(self):
        """Test camera parameter validation"""
        # Test invalid camera type
        with self.assertRaises(CameraError):
            JetsonCamera(camera_type="invalid")
        
        # Test IP camera without URL
        with self.assertRaises(CameraError):
            JetsonCamera(camera_type="ip", ip_url=None)
    
    @patch('cv2.VideoCapture')
    def test_usb_camera_connection(self, mock_videocapture):
        """Test USB camera connection"""
        # Mock successful connection
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, Mock())
        mock_videocapture.return_value = mock_cap
        
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        result = camera.connect()
        
        self.assertTrue(result)
        self.assertTrue(camera.is_connected)
        mock_videocapture.assert_called()
    
    @patch('cv2.VideoCapture')
    def test_camera_frame_capture(self, mock_videocapture):
        """Test camera frame capture"""
        import numpy as np
        
        # Mock successful frame capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        mock_videocapture.return_value = mock_cap
        
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        camera.connect()
        
        ret, frame = camera.capture_frame()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (480, 640, 3))
    
    def test_camera_info(self):
        """Test camera info retrieval"""
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        
        # Test info when not connected
        info = camera.get_camera_info()
        self.assertIn("error", info)
    
    def test_detect_cameras_function(self):
        """Test camera detection function"""
        detected = detect_cameras()
        
        # Should return a dictionary with camera types
        self.assertIsInstance(detected, dict)
        self.assertIn("usb", detected)
        self.assertIn("csi", detected)
        self.assertIsInstance(detected["usb"], list)
        self.assertIsInstance(detected["csi"], list)


class TestJetsonLidar(unittest.TestCase):
    """Test cases for JetsonLidar class"""
    
    def test_lidar_initialization(self):
        """Test LIDAR initialization with different parameters"""
        # Test generic serial LIDAR
        lidar = JetsonLidar(
            lidar_type=LidarType.GENERIC_SERIAL,
            port="/dev/ttyUSB0",
            baudrate=115200
        )
        self.assertEqual(lidar.lidar_type, LidarType.GENERIC_SERIAL)
        self.assertEqual(lidar.port, "/dev/ttyUSB0")
        self.assertEqual(lidar.baudrate, 115200)
        
        # Test RPLidar
        lidar = JetsonLidar(
            lidar_type=LidarType.RPLIDAR,
            port="/dev/ttyUSB1",
            baudrate=115200
        )
        self.assertEqual(lidar.lidar_type, LidarType.RPLIDAR)
        
        # Test network LIDAR
        lidar = JetsonLidar(
            lidar_type=LidarType.SICK_TIM,
            ip_address="192.168.1.10",
            ip_port=2111
        )
        self.assertEqual(lidar.lidar_type, LidarType.SICK_TIM)
        self.assertEqual(lidar.ip_address, "192.168.1.10")
    
    @patch('serial.Serial')
    def test_serial_lidar_connection(self, mock_serial):
        """Test serial LIDAR connection"""
        # Mock successful serial connection
        mock_conn = Mock()
        mock_conn.is_open = True
        mock_conn.write.return_value = None
        mock_conn.read.return_value = b'test_response'
        mock_conn.in_waiting = 0
        mock_serial.return_value = mock_conn
        
        lidar = JetsonLidar(
            lidar_type=LidarType.GENERIC_SERIAL,
            port="/dev/ttyUSB0"
        )
        
        result = lidar.connect()
        self.assertTrue(result)
        self.assertTrue(lidar.is_connected)
        mock_serial.assert_called_once()
    
    @patch('socket.socket')
    def test_network_lidar_connection(self, mock_socket):
        """Test network LIDAR connection"""
        # Mock successful network connection
        mock_sock = Mock()
        mock_sock.sendto.return_value = None
        mock_socket.return_value = mock_sock
        
        lidar = JetsonLidar(
            lidar_type=LidarType.SICK_TIM,
            ip_address="192.168.1.10",
            ip_port=2111
        )
        
        result = lidar.connect()
        self.assertTrue(result)
        self.assertTrue(lidar.is_connected)
    
    def test_lidar_device_info(self):
        """Test LIDAR device info retrieval"""
        lidar = JetsonLidar(
            lidar_type=LidarType.GENERIC_SERIAL,
            port="/dev/ttyUSB0"
        )
        
        info = lidar.get_device_info()
        self.assertIsInstance(info, dict)
        self.assertIn("lidar_type", info)
        self.assertIn("port", info)
        self.assertIn("is_connected", info)
    
    def test_detect_lidar_devices_function(self):
        """Test LIDAR detection function"""
        detected = detect_lidar_devices()
        
        # Should return a list of detected devices
        self.assertIsInstance(detected, list)
        
        # Each device should have required fields
        for device in detected:
            self.assertIn("port", device)
            self.assertIn("description", device)
            self.assertIn("type", device)


class TestJetsonSDK(unittest.TestCase):
    """Test cases for JetsonSDK class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_output_dir = Path("test_sdk_output")
        self.sdk = JetsonSDK(output_dir=str(self.test_output_dir))
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Cleanup SDK
        self.sdk.cleanup()
        
        # Clean up test files
        if self.test_output_dir.exists():
            for file in self.test_output_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir in sorted(self.test_output_dir.rglob("*"), reverse=True):
                if dir.is_dir():
                    dir.rmdir()
            self.test_output_dir.rmdir()
    
    def test_sdk_initialization(self):
        """Test SDK initialization"""
        self.assertIsInstance(self.sdk, JetsonSDK)
        self.assertTrue(self.test_output_dir.exists())
        self.assertIsInstance(self.sdk.stats, dict)
    
    def test_hardware_detection(self):
        """Test hardware detection"""
        hardware = self.sdk.detect_hardware()
        
        self.assertIsInstance(hardware, dict)
        self.assertIn("cameras", hardware)
        self.assertIn("lidars", hardware)
        self.assertIn("timestamp", hardware)
        
        # Check if detection results are saved
        detection_file = self.test_output_dir / "hardware_detection.json"
        self.assertTrue(detection_file.exists())
    
    @patch.object(JetsonCamera, 'connect')
    @patch.object(JetsonCamera, 'get_camera_info')
    def test_camera_setup(self, mock_get_info, mock_connect):
        """Test camera setup"""
        # Mock successful camera setup
        mock_connect.return_value = True
        mock_get_info.return_value = {"camera_type": "usb", "is_connected": True}
        
        result = self.sdk.setup_camera("usb", 0)
        self.assertTrue(result)
        self.assertIsNotNone(self.sdk.camera)
    
    @patch.object(JetsonLidar, 'connect')
    @patch.object(JetsonLidar, 'get_device_info')
    def test_lidar_setup(self, mock_get_info, mock_connect):
        """Test LIDAR setup"""
        # Mock successful LIDAR setup
        mock_connect.return_value = True
        mock_get_info.return_value = {"lidar_type": "generic_serial", "is_connected": True}
        
        result = self.sdk.setup_lidar("generic_serial", "/dev/ttyUSB0")
        self.assertTrue(result)
        self.assertIsNotNone(self.sdk.lidar)
    
    def test_statistics(self):
        """Test statistics tracking"""
        stats = self.sdk.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("images_captured", stats)
        self.assertIn("lidar_scans", stats)
        self.assertIn("errors", stats)
    
    @patch.object(JetsonCamera, 'capture_frame')
    @patch.object(JetsonLidar, 'get_single_measurement')
    def test_single_data_capture(self, mock_lidar_measure, mock_camera_capture):
        """Test single data capture"""
        import numpy as np
        from lidar import LidarPoint
        
        # Mock camera and LIDAR
        self.sdk.camera = Mock()
        self.sdk.lidar = Mock()
        
        # Mock successful captures
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera_capture.return_value = (True, test_frame)
        
        test_point = LidarPoint(angle=0.0, distance=1000.0, quality=255, timestamp=time.time())
        mock_lidar_measure.return_value = test_point
        
        data = self.sdk.capture_single_data()
        
        self.assertIsInstance(data, dict)
        self.assertIn("timestamp", data)
        self.assertIn("camera", data)
        self.assertIn("lidar", data)
        self.assertIn("errors", data)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling"""
    
    def test_camera_connection_failure(self):
        """Test camera connection failure handling"""
        camera = JetsonCamera(camera_type="usb", camera_id=999)  # Non-existent camera
        
        result = camera.connect()
        self.assertFalse(result)
        self.assertFalse(camera.is_connected)
    
    def test_lidar_connection_failure(self):
        """Test LIDAR connection failure handling"""
        lidar = JetsonLidar(
            lidar_type=LidarType.GENERIC_SERIAL,
            port="/dev/nonexistent"  # Non-existent port
        )
        
        result = lidar.connect()
        self.assertFalse(result)
        self.assertFalse(lidar.is_connected)
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        # Invalid camera type
        with self.assertRaises(CameraError):
            JetsonCamera(camera_type="invalid_type")
        
        # IP camera without URL
        with self.assertRaises(CameraError):
            JetsonCamera(camera_type="ip", ip_url=None)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_output_dir = Path("test_integration_output")
        self.sdk = JetsonSDK(output_dir=str(self.test_output_dir))
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        self.sdk.cleanup()
        
        # Clean up test files
        if self.test_output_dir.exists():
            for file in self.test_output_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir in sorted(self.test_output_dir.rglob("*"), reverse=True):
                if dir.is_dir():
                    dir.rmdir()
            self.test_output_dir.rmdir()
    
    def test_full_workflow(self):
        """Test complete SDK workflow"""
        # Hardware detection
        hardware = self.sdk.detect_hardware()
        self.assertIsInstance(hardware, dict)
        
        # Statistics check
        stats = self.sdk.get_statistics()
        self.assertIsInstance(stats, dict)
        
        # Cleanup should work without errors
        self.sdk.cleanup()


def run_hardware_tests():
    """Run tests that require actual hardware"""
    logger.info("Running hardware-dependent tests...")
    
    # Test camera detection with real hardware
    logger.info("Testing camera detection...")
    cameras = detect_cameras()
    logger.info(f"Detected cameras: {cameras}")
    
    # Test LIDAR detection with real hardware
    logger.info("Testing LIDAR detection...")
    lidars = detect_lidar_devices()
    logger.info(f"Detected LIDAR devices: {lidars}")
    
    # Test actual camera connection if available
    if cameras["usb"]:
        logger.info("Testing USB camera connection...")
        camera = JetsonCamera(camera_type="usb", camera_id=cameras["usb"][0])
        if camera.connect():
            logger.info("USB camera connected successfully")
            
            # Test frame capture
            ret, frame = camera.capture_frame()
            if ret:
                logger.info(f"Frame captured: shape={frame.shape}")
            else:
                logger.warning("Failed to capture frame")
            
            camera.disconnect()
        else:
            logger.warning("Failed to connect to USB camera")
    
    # Test CSI camera if available
    if cameras["csi"]:
        logger.info("Testing CSI camera connection...")
        camera = JetsonCamera(camera_type="csi", camera_id=cameras["csi"][0])
        if camera.connect():
            logger.info("CSI camera connected successfully")
            camera.disconnect()
        else:
            logger.warning("Failed to connect to CSI camera")
    
    # Test LIDAR connection if available
    if lidars:
        logger.info("Testing LIDAR connection...")
        device = lidars[0]
        lidar_type_map = {
            "rplidar": LidarType.RPLIDAR,
            "ydlidar": LidarType.YDLIDAR,
            "hokuyo_urg": LidarType.HOKUYO_URG,
            "generic_serial": LidarType.GENERIC_SERIAL
        }
        
        lidar_type = lidar_type_map.get(device.get("likely_type"), LidarType.GENERIC_SERIAL)
        lidar = JetsonLidar(lidar_type=lidar_type, port=device["port"])
        
        if lidar.connect():
            logger.info("LIDAR connected successfully")
            
            # Test single measurement
            measurement = lidar.get_single_measurement()
            if measurement:
                logger.info(f"LIDAR measurement: {measurement.distance}mm at {measurement.angle}°")
            else:
                logger.warning("Failed to get LIDAR measurement")
            
            lidar.disconnect()
        else:
            logger.warning("Failed to connect to LIDAR")


def run_performance_tests():
    """Run performance tests"""
    logger.info("Running performance tests...")
    
    # Test SDK initialization time
    start_time = time.time()
    sdk = JetsonSDK(output_dir="perf_test_output")
    init_time = time.time() - start_time
    logger.info(f"SDK initialization time: {init_time:.3f}s")
    
    # Test hardware detection time
    start_time = time.time()
    hardware = sdk.detect_hardware()
    detection_time = time.time() - start_time
    logger.info(f"Hardware detection time: {detection_time:.3f}s")
    
    # Cleanup
    sdk.cleanup()
    
    # Clean up test files
    test_dir = Path("perf_test_output")
    if test_dir.exists():
        for file in test_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        for dir in sorted(test_dir.rglob("*"), reverse=True):
            if dir.is_dir():
                dir.rmdir()
        test_dir.rmdir()


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jetson Orin SDK Test Suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--hardware", action="store_true", help="Run hardware tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.all or not any([args.unit, args.hardware, args.performance]):
        args.unit = args.hardware = args.performance = True
    
    logger.info("Starting Jetson Orin SDK Test Suite")
    
    # Run unit tests
    if args.unit:
        logger.info("=" * 50)
        logger.info("RUNNING UNIT TESTS")
        logger.info("=" * 50)
        
        # Create test suite
        test_suite = unittest.TestSuite()
        
        # Add test cases using TestLoader (makeSuite is deprecated in Python 3.13+)
        loader = unittest.TestLoader()
        test_suite.addTest(loader.loadTestsFromTestCase(TestJetsonCamera))
        test_suite.addTest(loader.loadTestsFromTestCase(TestJetsonLidar))
        test_suite.addTest(loader.loadTestsFromTestCase(TestJetsonSDK))
        test_suite.addTest(loader.loadTestsFromTestCase(TestErrorHandling))
        test_suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(test_suite)
        
        if result.wasSuccessful():
            logger.info("All unit tests passed!")
        else:
            logger.error(f"Unit tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    
    # Run hardware tests
    if args.hardware:
        logger.info("=" * 50)
        logger.info("RUNNING HARDWARE TESTS")
        logger.info("=" * 50)
        
        try:
            run_hardware_tests()
            logger.info("Hardware tests completed!")
        except Exception as e:
            logger.error(f"Hardware tests failed: {e}")
    
    # Run performance tests
    if args.performance:
        logger.info("=" * 50)
        logger.info("RUNNING PERFORMANCE TESTS")
        logger.info("=" * 50)
        
        try:
            run_performance_tests()
            logger.info("Performance tests completed!")
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
    
    logger.info("Test suite completed!")


if __name__ == "__main__":
    main()