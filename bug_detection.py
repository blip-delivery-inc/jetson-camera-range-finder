#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Bug Detection Suite

This script specifically tests for potential bugs including:
- Race conditions
- Resource leaks
- Threading issues
- File handle leaks
- Memory corruption
- Edge case failures
- Error propagation issues

Author: Jetson Orin Integration SDK
"""

import os
import sys
import time
import threading
import gc
import tracemalloc
import tempfile
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

# Import SDK modules
from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, detect_lidar_devices, LidarType, LidarError
from main import JetsonSDK

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

class BugDetector:
    """Comprehensive bug detection for Jetson SDK"""
    
    def __init__(self):
        self.bugs_found = []
        self.warnings = []
        self.test_results = {}
    
    def log_bug(self, severity: str, description: str, details: str = ""):
        """Log a potential bug"""
        bug = {
            "severity": severity,
            "description": description,
            "details": details,
            "timestamp": time.time()
        }
        if severity == "CRITICAL" or severity == "HIGH":
            self.bugs_found.append(bug)
        else:
            self.warnings.append(bug)
        print(f"[{severity}] {description}")
        if details:
            print(f"    Details: {details}")
    
    def test_race_conditions(self):
        """Test for race conditions in concurrent operations"""
        print("\n=== Testing Race Conditions ===")
        
        # Test concurrent camera detection
        def concurrent_camera_detection():
            try:
                return detect_cameras()
            except Exception as e:
                return {"error": str(e)}
        
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_camera_detection) for _ in range(20)]
            for future in futures:
                results.append(future.result())
        
        # Check for inconsistent results
        unique_results = set(str(r) for r in results)
        if len(unique_results) > 1:
            self.log_bug("HIGH", "Race condition detected in camera detection", 
                        f"Got {len(unique_results)} different results from concurrent calls")
        
        # Test concurrent SDK initialization
        def concurrent_sdk_init():
            try:
                sdk = JetsonSDK(output_dir=f"race_test_{threading.current_thread().ident}")
                sdk.cleanup()
                return "success"
            except Exception as e:
                return str(e)
        
        sdk_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_sdk_init) for _ in range(10)]
            for future in futures:
                sdk_results.append(future.result())
        
        errors = [r for r in sdk_results if r != "success"]
        if errors:
            self.log_bug("MEDIUM", "Potential race condition in SDK initialization",
                        f"Errors in concurrent init: {errors[:3]}")
    
    def test_resource_leaks(self):
        """Test for resource leaks"""
        print("\n=== Testing Resource Leaks ===")
        
        # Test file handle leaks
        initial_fds = len(os.listdir('/proc/self/fd'))
        
        for i in range(50):
            try:
                sdk = JetsonSDK(output_dir=f"leak_test_{i}")
                hardware = sdk.detect_hardware()
                sdk.cleanup()
            except Exception:
                pass
        
        final_fds = len(os.listdir('/proc/self/fd'))
        fd_leak = final_fds - initial_fds
        
        if fd_leak > 5:  # Allow some tolerance
            self.log_bug("HIGH", "File descriptor leak detected",
                        f"Leaked {fd_leak} file descriptors")
        elif fd_leak > 0:
            self.log_bug("MEDIUM", "Potential file descriptor leak",
                        f"Possible leak of {fd_leak} file descriptors")
        
        # Test camera resource cleanup
        for i in range(20):
            try:
                camera = JetsonCamera(camera_type="usb", camera_id=0)
                camera.connect()  # Will fail but should cleanup
                camera.disconnect()
            except Exception:
                pass
        
        # Force garbage collection
        gc.collect()
    
    def test_threading_safety(self):
        """Test thread safety issues"""
        print("\n=== Testing Thread Safety ===")
        
        shared_sdk = JetsonSDK(output_dir="thread_safety_test")
        errors = []
        
        def worker_thread(thread_id):
            try:
                for i in range(10):
                    # These operations should be thread-safe
                    stats = shared_sdk.get_statistics()
                    hardware = shared_sdk.detect_hardware()
                    time.sleep(0.01)
                return "success"
            except Exception as e:
                return f"Thread {thread_id} error: {e}"
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(5)]
            for future in futures:
                result = future.result()
                if result != "success":
                    errors.append(result)
        
        shared_sdk.cleanup()
        
        if errors:
            self.log_bug("HIGH", "Thread safety issues detected",
                        f"Errors: {errors[:3]}")
    
    def test_error_propagation(self):
        """Test proper error handling and propagation"""
        print("\n=== Testing Error Propagation ===")
        
        # Test camera error propagation
        try:
            camera = JetsonCamera(camera_type="invalid_type")
            self.log_bug("HIGH", "Invalid camera type not caught during initialization")
        except CameraError:
            pass  # Expected
        except Exception as e:
            self.log_bug("MEDIUM", "Wrong exception type for invalid camera",
                        f"Got {type(e).__name__} instead of CameraError")
        
        # Test LIDAR error propagation
        try:
            lidar = JetsonLidar(lidar_type=LidarType.GENERIC_SERIAL, port="/dev/nonexistent")
            result = lidar.connect()
            if result:  # Should return False, not throw
                self.log_bug("MEDIUM", "LIDAR connection should fail for nonexistent port")
        except Exception as e:
            # Connection should return False, not throw exception
            self.log_bug("LOW", "LIDAR connection throws exception instead of returning False",
                        f"Exception: {e}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n=== Testing Edge Cases ===")
        
        # Test empty/None parameters
        test_cases = [
            {"test": "Empty string camera type", "params": {"camera_type": ""}},
            {"test": "None IP URL", "params": {"camera_type": "ip", "ip_url": None}},
            {"test": "Negative camera ID", "params": {"camera_type": "usb", "camera_id": -1}},
            {"test": "Very large camera ID", "params": {"camera_type": "usb", "camera_id": 999999}},
        ]
        
        for case in test_cases:
            try:
                camera = JetsonCamera(**case["params"])
                result = camera.connect()
                # Should handle gracefully without crashing
            except Exception as e:
                if "Invalid" not in str(e) and "Unsupported" not in str(e):
                    self.log_bug("MEDIUM", f"Unexpected exception in {case['test']}",
                                f"Exception: {e}")
        
        # Test SDK with invalid output directory
        try:
            sdk = JetsonSDK(output_dir="/root/invalid_permission_dir")
            # Should handle gracefully
        except PermissionError:
            pass  # Expected
        except Exception as e:
            self.log_bug("LOW", "SDK should handle permission errors gracefully",
                        f"Exception: {e}")
    
    def test_memory_corruption(self):
        """Test for potential memory corruption issues"""
        print("\n=== Testing Memory Corruption ===")
        
        # Test with invalid frame data
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        
        # Mock a corrupted frame scenario
        with patch.object(camera, 'cap') as mock_cap:
            mock_cap.read.return_value = (True, None)  # Valid return but None frame
            mock_cap.isOpened.return_value = True
            camera.is_connected = True
            
            try:
                ret, frame = camera.capture_frame()
                if ret:  # Should return False for None frame
                    self.log_bug("MEDIUM", "Camera returns success for None frame")
            except Exception as e:
                self.log_bug("LOW", "Camera should handle None frame gracefully",
                            f"Exception: {e}")
    
    def test_cleanup_completeness(self):
        """Test that cleanup is complete and doesn't leave resources"""
        print("\n=== Testing Cleanup Completeness ===")
        
        # Test SDK cleanup
        temp_dir = tempfile.mkdtemp()
        sdk = JetsonSDK(output_dir=temp_dir)
        
        # Create some test data
        hardware = sdk.detect_hardware()
        
        # Cleanup
        sdk.cleanup()
        
        # Check if temporary files are cleaned up
        remaining_files = list(Path(temp_dir).rglob("*"))
        if len(remaining_files) > 2:  # Allow for basic structure
            self.log_bug("LOW", "SDK cleanup may not remove all temporary files",
                        f"Remaining files: {len(remaining_files)}")
        
        # Test camera cleanup
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        camera.connect()  # Will fail but should not crash
        camera.disconnect()
        
        if hasattr(camera, 'cap') and camera.cap is not None:
            try:
                if camera.cap.isOpened():
                    self.log_bug("MEDIUM", "Camera not properly closed after disconnect")
            except:
                pass  # Cap might be invalid, which is okay
    
    def test_timestamp_consistency(self):
        """Test timestamp consistency and potential race conditions"""
        print("\n=== Testing Timestamp Consistency ===")
        
        sdk = JetsonSDK(output_dir="timestamp_test")
        
        # Capture multiple data points rapidly
        timestamps = []
        for i in range(10):
            data = sdk.capture_single_data()
            timestamps.append(data.get("timestamp", 0))
            time.sleep(0.001)  # Very small delay
        
        sdk.cleanup()
        
        # Check for timestamp ordering
        for i in range(1, len(timestamps)):
            if timestamps[i] <= timestamps[i-1]:
                self.log_bug("LOW", "Timestamp ordering issue detected",
                            f"Timestamp {i}: {timestamps[i]} <= {timestamps[i-1]}")
                break
    
    def test_import_issues(self):
        """Test for potential import-related bugs"""
        print("\n=== Testing Import Issues ===")
        
        # Test importing cv2 inside functions (potential issue)
        import main
        import inspect
        
        source = inspect.getsource(main.JetsonSDK.capture_single_data)
        if "import cv2" in source:
            self.log_bug("LOW", "cv2 imported inside function instead of module level",
                        "This could cause performance issues in tight loops")
    
    def run_all_tests(self):
        """Run all bug detection tests"""
        print("Starting comprehensive bug detection...")
        print("=" * 50)
        
        test_methods = [
            self.test_race_conditions,
            self.test_resource_leaks,
            self.test_threading_safety,
            self.test_error_propagation,
            self.test_edge_cases,
            self.test_memory_corruption,
            self.test_cleanup_completeness,
            self.test_timestamp_consistency,
            self.test_import_issues
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_bug("CRITICAL", f"Bug detection test failed: {test_method.__name__}",
                            f"Exception: {e}")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate bug detection report"""
        print("\n" + "=" * 50)
        print("BUG DETECTION REPORT")
        print("=" * 50)
        
        if not self.bugs_found and not self.warnings:
            print("✅ NO BUGS DETECTED!")
            print("The SDK appears to be free of major bugs.")
        else:
            if self.bugs_found:
                print(f"🐛 BUGS FOUND: {len(self.bugs_found)}")
                for bug in self.bugs_found:
                    print(f"  [{bug['severity']}] {bug['description']}")
                    if bug['details']:
                        print(f"      {bug['details']}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
                for warning in self.warnings:
                    print(f"  [{warning['severity']}] {warning['description']}")
                    if warning['details']:
                        print(f"      {warning['details']}")
        
        print("\n" + "=" * 50)
        
        # Return summary
        return {
            "bugs_found": len(self.bugs_found),
            "warnings": len(self.warnings),
            "critical_bugs": len([b for b in self.bugs_found if b['severity'] == 'CRITICAL']),
            "high_bugs": len([b for b in self.bugs_found if b['severity'] == 'HIGH']),
            "medium_bugs": len([b for b in self.bugs_found + self.warnings if b['severity'] == 'MEDIUM']),
            "low_issues": len([b for b in self.bugs_found + self.warnings if b['severity'] == 'LOW'])
        }


def main():
    """Main bug detection function"""
    detector = BugDetector()
    summary = detector.run_all_tests()
    
    # Exit with error code if critical bugs found
    if summary['critical_bugs'] > 0:
        sys.exit(2)
    elif summary['bugs_found'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()