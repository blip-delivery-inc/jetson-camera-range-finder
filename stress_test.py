#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Stress Test Suite

This script performs comprehensive stress testing including:
- Memory leak detection
- Concurrent operations
- Error injection and recovery
- Edge case testing
- Resource exhaustion testing
- Long-running stability tests

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import os
import sys
import time
import json
import logging
import threading
import gc
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import SDK modules
from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, detect_lidar_devices, LidarType, LidarError
from main import JetsonSDK

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StressTestSuite:
    """Comprehensive stress testing suite for Jetson SDK"""
    
    def __init__(self, output_dir: str = "stress_test_results"):
        """Initialize stress test suite"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "memory_tests": {},
            "concurrency_tests": {},
            "error_handling_tests": {},
            "edge_case_tests": {},
            "stability_tests": {},
            "resource_exhaustion_tests": {}
        }
        
        logger.info(f"Stress test suite initialized. Results will be saved to: {self.output_dir}")
    
    def test_memory_leaks(self, iterations: int = 100) -> Dict[str, Any]:
        """Test for memory leaks in SDK operations"""
        logger.info(f"Testing memory leaks with {iterations} iterations...")
        
        # Start memory tracing
        tracemalloc.start()
        
        results = {
            "iterations": iterations,
            "initial_memory_mb": 0,
            "final_memory_mb": 0,
            "peak_memory_mb": 0,
            "memory_growth_mb": 0,
            "potential_leak": False
        }
        
        # Get initial memory usage
        gc.collect()
        initial_snapshot = tracemalloc.take_snapshot()
        initial_stats = initial_snapshot.statistics('lineno')
        results["initial_memory_mb"] = sum(stat.size for stat in initial_stats) / 1024 / 1024
        
        peak_memory = results["initial_memory_mb"]
        
        # Run iterations
        for i in range(iterations):
            try:
                # Test camera operations
                cameras = detect_cameras()
                
                # Test LIDAR operations  
                lidars = detect_lidar_devices()
                
                # Test SDK initialization and cleanup
                sdk = JetsonSDK(output_dir=str(self.output_dir / f"memory_test_{i}"))
                hardware = sdk.detect_hardware()
                sdk.cleanup()
                
                # Monitor memory every 10 iterations
                if i % 10 == 0:
                    gc.collect()
                    current_snapshot = tracemalloc.take_snapshot()
                    current_stats = current_snapshot.statistics('lineno')
                    current_memory = sum(stat.size for stat in current_stats) / 1024 / 1024
                    peak_memory = max(peak_memory, current_memory)
                    
                    logger.info(f"Iteration {i}: Memory usage: {current_memory:.2f} MB")
                
            except Exception as e:
                logger.warning(f"Error in iteration {i}: {e}")
        
        # Final memory check
        gc.collect()
        final_snapshot = tracemalloc.take_snapshot()
        final_stats = final_snapshot.statistics('lineno')
        results["final_memory_mb"] = sum(stat.size for stat in final_stats) / 1024 / 1024
        results["peak_memory_mb"] = peak_memory
        results["memory_growth_mb"] = results["final_memory_mb"] - results["initial_memory_mb"]
        
        # Check for potential memory leak (>10MB growth)
        results["potential_leak"] = results["memory_growth_mb"] > 10.0
        
        tracemalloc.stop()
        
        logger.info(f"Memory test completed. Growth: {results['memory_growth_mb']:.2f} MB")
        return results
    
    def test_concurrent_operations(self, num_threads: int = 10, duration: int = 30) -> Dict[str, Any]:
        """Test concurrent SDK operations"""
        logger.info(f"Testing concurrent operations with {num_threads} threads for {duration}s...")
        
        results = {
            "num_threads": num_threads,
            "duration": duration,
            "successful_operations": 0,
            "failed_operations": 0,
            "exceptions": [],
            "thread_results": []
        }
        
        def worker_thread(thread_id: int) -> Dict[str, Any]:
            """Worker thread function"""
            thread_result = {
                "thread_id": thread_id,
                "operations": 0,
                "errors": 0,
                "exceptions": []
            }
            
            start_time = time.time()
            while (time.time() - start_time) < duration:
                try:
                    # Random operations
                    operation = thread_id % 4
                    
                    if operation == 0:
                        # Camera detection
                        cameras = detect_cameras()
                        thread_result["operations"] += 1
                        
                    elif operation == 1:
                        # LIDAR detection
                        lidars = detect_lidar_devices()
                        thread_result["operations"] += 1
                        
                    elif operation == 2:
                        # SDK initialization
                        sdk = JetsonSDK(output_dir=str(self.output_dir / f"concurrent_{thread_id}"))
                        sdk.cleanup()
                        thread_result["operations"] += 1
                        
                    elif operation == 3:
                        # Camera object creation/destruction
                        camera = JetsonCamera(camera_type="usb", camera_id=0)
                        info = camera.get_camera_info()
                        camera.disconnect()
                        thread_result["operations"] += 1
                    
                    time.sleep(0.01)  # Small delay
                    
                except Exception as e:
                    thread_result["errors"] += 1
                    thread_result["exceptions"].append(str(e))
            
            return thread_result
        
        # Run concurrent threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    thread_result = future.result()
                    results["thread_results"].append(thread_result)
                    results["successful_operations"] += thread_result["operations"]
                    results["failed_operations"] += thread_result["errors"]
                    results["exceptions"].extend(thread_result["exceptions"])
                except Exception as e:
                    results["failed_operations"] += 1
                    results["exceptions"].append(str(e))
        
        logger.info(f"Concurrent test completed. Success: {results['successful_operations']}, Errors: {results['failed_operations']}")
        return results
    
    def test_error_injection(self) -> Dict[str, Any]:
        """Test error handling and recovery"""
        logger.info("Testing error injection and recovery...")
        
        results = {
            "invalid_camera_tests": {},
            "invalid_lidar_tests": {},
            "resource_exhaustion_tests": {},
            "corruption_tests": {}
        }
        
        # Test invalid camera parameters
        invalid_camera_tests = []
        
        test_cases = [
            {"camera_type": "invalid", "camera_id": 0},
            {"camera_type": "usb", "camera_id": -1},
            {"camera_type": "usb", "camera_id": 9999},
            {"camera_type": "ip", "ip_url": None},
            {"camera_type": "ip", "ip_url": "invalid_url"},
            {"camera_type": "csi", "camera_id": -1}
        ]
        
        for test_case in test_cases:
            try:
                camera = JetsonCamera(**test_case)
                result = camera.connect()
                invalid_camera_tests.append({
                    "test_case": test_case,
                    "exception_raised": False,
                    "connection_result": result
                })
            except Exception as e:
                invalid_camera_tests.append({
                    "test_case": test_case,
                    "exception_raised": True,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                })
        
        results["invalid_camera_tests"] = invalid_camera_tests
        
        # Test invalid LIDAR parameters
        invalid_lidar_tests = []
        
        lidar_test_cases = [
            {"lidar_type": LidarType.GENERIC_SERIAL, "port": "/dev/nonexistent"},
            {"lidar_type": LidarType.GENERIC_SERIAL, "port": "/dev/null"},
            {"lidar_type": LidarType.SICK_TIM, "ip_address": "invalid_ip", "ip_port": 2111},
            {"lidar_type": LidarType.SICK_TIM, "ip_address": "127.0.0.1", "ip_port": -1}
        ]
        
        for test_case in lidar_test_cases:
            try:
                lidar = JetsonLidar(**test_case)
                result = lidar.connect()
                lidar.disconnect()
                invalid_lidar_tests.append({
                    "test_case": str(test_case),
                    "exception_raised": False,
                    "connection_result": result
                })
            except Exception as e:
                invalid_lidar_tests.append({
                    "test_case": str(test_case),
                    "exception_raised": True,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                })
        
        results["invalid_lidar_tests"] = invalid_lidar_tests
        
        logger.info("Error injection tests completed")
        return results
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and boundary conditions"""
        logger.info("Testing edge cases...")
        
        results = {
            "boundary_tests": [],
            "null_tests": [],
            "extreme_value_tests": []
        }
        
        # Boundary value tests
        boundary_tests = []
        
        # Test extreme resolutions
        extreme_resolutions = [
            (1, 1), (32000, 32000), (0, 480), (640, 0)
        ]
        
        for width, height in extreme_resolutions:
            try:
                camera = JetsonCamera(camera_type="usb", camera_id=0, width=width, height=height)
                boundary_tests.append({
                    "test": f"Resolution {width}x{height}",
                    "success": True,
                    "exception": None
                })
            except Exception as e:
                boundary_tests.append({
                    "test": f"Resolution {width}x{height}",
                    "success": False,
                    "exception": str(e)
                })
        
        # Test extreme FPS values
        extreme_fps = [-1, 0, 1, 1000, 999999]
        
        for fps in extreme_fps:
            try:
                camera = JetsonCamera(camera_type="usb", camera_id=0, fps=fps)
                boundary_tests.append({
                    "test": f"FPS {fps}",
                    "success": True,
                    "exception": None
                })
            except Exception as e:
                boundary_tests.append({
                    "test": f"FPS {fps}",
                    "success": False,
                    "exception": str(e)
                })
        
        results["boundary_tests"] = boundary_tests
        
        # Test null/None values
        null_tests = []
        
        try:
            sdk = JetsonSDK(output_dir=None)
            null_tests.append({"test": "None output_dir", "success": True})
        except Exception as e:
            null_tests.append({"test": "None output_dir", "success": False, "exception": str(e)})
        
        results["null_tests"] = null_tests
        
        logger.info("Edge case tests completed")
        return results
    
    def test_stability(self, duration: int = 60) -> Dict[str, Any]:
        """Test long-running stability"""
        logger.info(f"Testing stability for {duration} seconds...")
        
        results = {
            "duration": duration,
            "operations_completed": 0,
            "errors_encountered": 0,
            "error_details": [],
            "performance_degradation": False
        }
        
        start_time = time.time()
        operation_times = []
        
        while (time.time() - start_time) < duration:
            try:
                operation_start = time.time()
                
                # Perform various operations
                cameras = detect_cameras()
                lidars = detect_lidar_devices()
                
                sdk = JetsonSDK(output_dir=str(self.output_dir / "stability_test"))
                hardware = sdk.detect_hardware()
                sdk.cleanup()
                
                operation_time = time.time() - operation_start
                operation_times.append(operation_time)
                results["operations_completed"] += 1
                
                # Check for performance degradation
                if len(operation_times) > 10:
                    recent_avg = sum(operation_times[-10:]) / 10
                    initial_avg = sum(operation_times[:10]) / 10
                    if recent_avg > initial_avg * 2:  # 100% increase
                        results["performance_degradation"] = True
                
                time.sleep(0.5)  # 2 operations per second
                
            except Exception as e:
                results["errors_encountered"] += 1
                results["error_details"].append({
                    "timestamp": time.time() - start_time,
                    "error": str(e)
                })
        
        results["average_operation_time"] = sum(operation_times) / len(operation_times) if operation_times else 0
        
        logger.info(f"Stability test completed. Operations: {results['operations_completed']}, Errors: {results['errors_encountered']}")
        return results
    
    def test_resource_exhaustion(self) -> Dict[str, Any]:
        """Test behavior under resource exhaustion"""
        logger.info("Testing resource exhaustion scenarios...")
        
        results = {
            "file_descriptor_test": {},
            "memory_pressure_test": {},
            "thread_exhaustion_test": {}
        }
        
        # Test file descriptor exhaustion
        try:
            file_handles = []
            for i in range(1000):  # Try to open many files
                try:
                    fh = open(f"/tmp/test_fd_{i}", "w")
                    file_handles.append(fh)
                except OSError as e:
                    results["file_descriptor_test"] = {
                        "files_opened": len(file_handles),
                        "error": str(e),
                        "handled_gracefully": True
                    }
                    break
            
            # Cleanup
            for fh in file_handles:
                try:
                    fh.close()
                    os.unlink(fh.name)
                except:
                    pass
                    
        except Exception as e:
            results["file_descriptor_test"] = {
                "error": str(e),
                "handled_gracefully": False
            }
        
        # Test memory pressure (allocate large arrays)
        try:
            large_arrays = []
            for i in range(100):
                try:
                    # Allocate 10MB arrays
                    arr = [0] * (10 * 1024 * 1024 // 8)  # 10MB of integers
                    large_arrays.append(arr)
                except MemoryError as e:
                    results["memory_pressure_test"] = {
                        "arrays_allocated": len(large_arrays),
                        "error": str(e),
                        "handled_gracefully": True
                    }
                    break
            
            # Cleanup
            del large_arrays
            gc.collect()
            
        except Exception as e:
            results["memory_pressure_test"] = {
                "error": str(e),
                "handled_gracefully": False
            }
        
        logger.info("Resource exhaustion tests completed")
        return results
    
    def run_all_stress_tests(self) -> Dict[str, Any]:
        """Run complete stress test suite"""
        logger.info("Starting comprehensive stress test suite...")
        
        try:
            # Memory leak tests
            self.results["memory_tests"] = self.test_memory_leaks(100)
            
            # Concurrency tests
            self.results["concurrency_tests"] = self.test_concurrent_operations(5, 15)
            
            # Error handling tests
            self.results["error_handling_tests"] = self.test_error_injection()
            
            # Edge case tests
            self.results["edge_case_tests"] = self.test_edge_cases()
            
            # Stability tests
            self.results["stability_tests"] = self.test_stability(30)
            
            # Resource exhaustion tests
            self.results["resource_exhaustion_tests"] = self.test_resource_exhaustion()
            
        except Exception as e:
            logger.error(f"Stress test suite failed: {e}")
            self.results["fatal_error"] = str(e)
        
        # Save results
        results_file = self.output_dir / f"stress_test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Stress test suite completed. Results saved to: {results_file}")
        return self.results
    
    def generate_stress_report(self) -> str:
        """Generate human-readable stress test report"""
        report = []
        report.append("=" * 60)
        report.append("JETSON ORIN SDK STRESS TEST REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {self.results['timestamp']}")
        report.append("")
        
        # Memory tests
        memory_tests = self.results.get("memory_tests", {})
        if memory_tests:
            report.append("MEMORY LEAK TESTS:")
            report.append(f"  Iterations: {memory_tests.get('iterations', 0)}")
            report.append(f"  Memory Growth: {memory_tests.get('memory_growth_mb', 0):.2f} MB")
            report.append(f"  Peak Memory: {memory_tests.get('peak_memory_mb', 0):.2f} MB")
            report.append(f"  Potential Leak: {'YES' if memory_tests.get('potential_leak', False) else 'NO'}")
            report.append("")
        
        # Concurrency tests
        concurrency_tests = self.results.get("concurrency_tests", {})
        if concurrency_tests:
            report.append("CONCURRENCY TESTS:")
            report.append(f"  Threads: {concurrency_tests.get('num_threads', 0)}")
            report.append(f"  Duration: {concurrency_tests.get('duration', 0)}s")
            report.append(f"  Successful Operations: {concurrency_tests.get('successful_operations', 0)}")
            report.append(f"  Failed Operations: {concurrency_tests.get('failed_operations', 0)}")
            report.append(f"  Success Rate: {concurrency_tests.get('successful_operations', 0) / (concurrency_tests.get('successful_operations', 0) + concurrency_tests.get('failed_operations', 0) + 1) * 100:.1f}%")
            report.append("")
        
        # Error handling tests
        error_tests = self.results.get("error_handling_tests", {})
        if error_tests:
            report.append("ERROR HANDLING TESTS:")
            report.append(f"  Invalid Camera Tests: {len(error_tests.get('invalid_camera_tests', []))}")
            report.append(f"  Invalid LIDAR Tests: {len(error_tests.get('invalid_lidar_tests', []))}")
            report.append("")
        
        # Stability tests
        stability_tests = self.results.get("stability_tests", {})
        if stability_tests:
            report.append("STABILITY TESTS:")
            report.append(f"  Duration: {stability_tests.get('duration', 0)}s")
            report.append(f"  Operations Completed: {stability_tests.get('operations_completed', 0)}")
            report.append(f"  Errors: {stability_tests.get('errors_encountered', 0)}")
            report.append(f"  Performance Degradation: {'YES' if stability_tests.get('performance_degradation', False) else 'NO'}")
            report.append(f"  Average Operation Time: {stability_tests.get('average_operation_time', 0):.3f}s")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main stress test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jetson Orin SDK Stress Test Suite")
    parser.add_argument("--output-dir", default="stress_test_results", help="Output directory")
    parser.add_argument("--memory-only", action="store_true", help="Run memory tests only")
    parser.add_argument("--concurrency-only", action="store_true", help="Run concurrency tests only")
    parser.add_argument("--error-only", action="store_true", help="Run error handling tests only")
    parser.add_argument("--stability-only", action="store_true", help="Run stability tests only")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (reduced iterations/duration)")
    
    args = parser.parse_args()
    
    # Initialize stress test suite
    stress_test = StressTestSuite(output_dir=args.output_dir)
    
    try:
        if args.memory_only:
            iterations = 50 if args.quick else 100
            logger.info("Running memory tests only...")
            stress_test.results["memory_tests"] = stress_test.test_memory_leaks(iterations)
            
        elif args.concurrency_only:
            threads = 5 if args.quick else 10
            duration = 15 if args.quick else 30
            logger.info("Running concurrency tests only...")
            stress_test.results["concurrency_tests"] = stress_test.test_concurrent_operations(threads, duration)
            
        elif args.error_only:
            logger.info("Running error handling tests only...")
            stress_test.results["error_handling_tests"] = stress_test.test_error_injection()
            
        elif args.stability_only:
            duration = 30 if args.quick else 60
            logger.info("Running stability tests only...")
            stress_test.results["stability_tests"] = stress_test.test_stability(duration)
            
        else:
            # Run all tests
            if args.quick:
                logger.info("Running quick stress test suite...")
                # Reduce test parameters for quick run
                stress_test.results["memory_tests"] = stress_test.test_memory_leaks(50)
                stress_test.results["concurrency_tests"] = stress_test.test_concurrent_operations(5, 10)
                stress_test.results["error_handling_tests"] = stress_test.test_error_injection()
                stress_test.results["edge_case_tests"] = stress_test.test_edge_cases()
                stress_test.results["stability_tests"] = stress_test.test_stability(20)
                stress_test.results["resource_exhaustion_tests"] = stress_test.test_resource_exhaustion()
            else:
                results = stress_test.run_all_stress_tests()
        
        # Generate and display report
        report = stress_test.generate_stress_report()
        print("\n" + report)
        
        # Save report to file
        report_file = stress_test.output_dir / f"stress_test_report_{int(time.time())}.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        logger.info(f"Stress test report saved to: {report_file}")
        
    except KeyboardInterrupt:
        logger.info("Stress tests interrupted by user")
    except Exception as e:
        logger.error(f"Stress tests failed: {e}")


if __name__ == "__main__":
    main()