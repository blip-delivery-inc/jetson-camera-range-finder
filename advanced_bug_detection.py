#!/usr/bin/env python3
"""
Advanced Bug Detection for Jetson Orin Integration SDK

This script performs deep code analysis to find:
- State management issues
- Resource handling problems  
- Logic errors
- Thread safety issues
- Performance problems
- Security vulnerabilities
"""

import ast
import os
import re
import sys
import inspect
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

# Import SDK modules for analysis
from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, detect_lidar_devices, LidarType, LidarError  
from main import JetsonSDK

logging.basicConfig(level=logging.WARNING)

class AdvancedBugDetector:
    """Advanced static and dynamic analysis for bug detection"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.code_files = ["main.py", "camera.py", "lidar.py"]
        
    def log_issue(self, severity: str, category: str, description: str, file: str = "", line: int = 0):
        """Log a detected issue"""
        issue = {
            "severity": severity,
            "category": category, 
            "description": description,
            "file": file,
            "line": line
        }
        
        if severity in ["CRITICAL", "HIGH"]:
            self.issues.append(issue)
        else:
            self.warnings.append(issue)
            
        print(f"[{severity}] {category}: {description}")
        if file:
            print(f"    File: {file}:{line}")

    def analyze_state_management(self):
        """Analyze state management issues"""
        print("\n=== Analyzing State Management ===")
        
        # Check camera state consistency
        camera = JetsonCamera(camera_type="usb", camera_id=0)
        
        # Test state after failed connection
        result = camera.connect()  # Will fail in test environment
        if not result and camera.is_connected:
            self.log_issue("HIGH", "State Management", 
                          "Camera is_connected=True after failed connection", 
                          "camera.py")
        
        # Test disconnect without connection
        camera.disconnect()
        if hasattr(camera, 'cap') and camera.cap is not None:
            try:
                if camera.cap.isOpened():
                    self.log_issue("MEDIUM", "State Management",
                                  "Camera capture object not properly cleaned up",
                                  "camera.py")
            except:
                pass  # Expected if cap is invalid
    
    def analyze_resource_leaks(self):
        """Deep analysis of resource management"""
        print("\n=== Analyzing Resource Management ===")
        
        # Test multiple SDK instances
        sdks = []
        for i in range(5):
            try:
                sdk = JetsonSDK(output_dir=f"resource_test_{i}")
                sdks.append(sdk)
            except Exception as e:
                self.log_issue("MEDIUM", "Resource Management",
                              f"Failed to create SDK instance {i}: {e}")
        
        # Check if all can be cleaned up properly
        for i, sdk in enumerate(sdks):
            try:
                sdk.cleanup()
            except Exception as e:
                self.log_issue("HIGH", "Resource Management",
                              f"Failed to cleanup SDK instance {i}: {e}")
    
    def analyze_thread_safety_deep(self):
        """Deep thread safety analysis"""
        print("\n=== Deep Thread Safety Analysis ===")
        
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        # Test shared state modifications
        sdk = JetsonSDK(output_dir="thread_test")
        errors = []
        
        def modify_stats():
            for i in range(100):
                try:
                    stats = sdk.get_statistics()
                    # Simulate state modification
                    stats["test_counter"] = stats.get("test_counter", 0) + 1
                    time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Stats modification error: {e}")
        
        # Run concurrent modifications
        threads = []
        for i in range(3):
            t = threading.Thread(target=modify_stats)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        if errors:
            self.log_issue("HIGH", "Thread Safety",
                          f"Concurrent state modification errors: {len(errors)}")
        
        sdk.cleanup()
    
    def analyze_error_handling_logic(self):
        """Analyze error handling patterns"""
        print("\n=== Analyzing Error Handling Logic ===")
        
        # Check for swallowed exceptions
        for file_path in self.code_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for bare except clauses
                    if re.search(r'except\s*:', line):
                        self.log_issue("MEDIUM", "Error Handling",
                                      "Bare except clause can hide errors",
                                      file_path, i)
                    
                    # Look for except blocks with only pass
                    if 'except' in line and i < len(lines):
                        next_lines = lines[i:i+3]
                        if any('pass' in nl.strip() and len(nl.strip()) <= 10 for nl in next_lines):
                            if not any('logger' in nl or 'print' in nl for nl in next_lines):
                                self.log_issue("LOW", "Error Handling",
                                              "Exception caught but not logged",
                                              file_path, i)
    
    def analyze_data_validation(self):
        """Analyze input validation and data handling"""
        print("\n=== Analyzing Data Validation ===")
        
        # Test camera with extreme values
        test_cases = [
            {"camera_type": "usb", "camera_id": -999999},
            {"camera_type": "usb", "camera_id": 999999},
            {"camera_type": "csi", "camera_id": -1},
            {"camera_type": "ip", "ip_url": ""},
            {"camera_type": "ip", "ip_url": "invalid_url"},
        ]
        
        for case in test_cases:
            try:
                camera = JetsonCamera(**case)
                result = camera.connect()
                # Should handle gracefully without crashing
                camera.disconnect()
            except ValueError as e:
                # Expected for some cases
                continue
            except Exception as e:
                self.log_issue("MEDIUM", "Data Validation",
                              f"Unexpected exception for {case}: {e}")
    
    def analyze_memory_usage_patterns(self):
        """Analyze memory usage patterns"""
        print("\n=== Analyzing Memory Usage ===")
        
        import tracemalloc
        import gc
        
        tracemalloc.start()
        
        # Create and destroy multiple objects
        objects = []
        for i in range(20):
            sdk = JetsonSDK(output_dir=f"mem_test_{i}")
            objects.append(sdk)
        
        # Take memory snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Cleanup objects
        for obj in objects:
            obj.cleanup()
        objects.clear()
        gc.collect()
        
        # Take another snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Compare memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Check for significant memory growth
        for stat in top_stats[:5]:
            if stat.size_diff > 1024 * 1024:  # 1MB growth
                self.log_issue("MEDIUM", "Memory Usage",
                              f"Potential memory leak: {stat.size_diff} bytes growth")
        
        tracemalloc.stop()
    
    def analyze_race_conditions_advanced(self):
        """Advanced race condition detection"""
        print("\n=== Advanced Race Condition Analysis ===")
        
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        # Test concurrent camera operations
        results = []
        
        def camera_operations():
            try:
                cameras = detect_cameras()
                return str(cameras)
            except Exception as e:
                return f"Error: {e}"
        
        # Run many concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(camera_operations) for _ in range(50)]
            results = [f.result() for f in futures]
        
        # Check for inconsistent results (potential race condition)
        unique_results = set(results)
        error_results = [r for r in results if r.startswith("Error:")]
        
        if len(unique_results) > 2:  # Allow some variation
            self.log_issue("MEDIUM", "Race Conditions",
                          f"Inconsistent results from concurrent calls: {len(unique_results)} different outcomes")
        
        if len(error_results) > len(results) * 0.1:  # More than 10% errors
            self.log_issue("HIGH", "Race Conditions",
                          f"High error rate in concurrent operations: {len(error_results)}/{len(results)}")
    
    def analyze_code_quality_issues(self):
        """Analyze code quality and potential bugs"""
        print("\n=== Analyzing Code Quality ===")
        
        for file_path in self.code_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    # Check for potential integer division issues
                    if '//' in line and 'int(' not in line:
                        self.log_issue("LOW", "Code Quality",
                                      "Integer division - ensure this is intended",
                                      file_path, i)
                    
                    # Check for hardcoded paths
                    if '/dev/' in line and 'nonexistent' not in line:
                        if not any(word in line.lower() for word in ['test', 'example', 'demo']):
                            self.log_issue("LOW", "Code Quality",
                                          "Hardcoded device path - consider making configurable",
                                          file_path, i)
                    
                    # Check for magic numbers
                    numbers = re.findall(r'\b\d{3,}\b', line)
                    for num in numbers:
                        if int(num) > 100 and 'timeout' not in line.lower():
                            self.log_issue("LOW", "Code Quality",
                                          f"Magic number {num} - consider using named constant",
                                          file_path, i)
    
    def analyze_exception_safety(self):
        """Analyze exception safety"""
        print("\n=== Analyzing Exception Safety ===")
        
        import time
        
        # Test exception safety in critical operations
        sdk = JetsonSDK(output_dir="exception_test")
        
        # Test what happens if capture fails during continuous operation
        try:
            # Mock a failure scenario
            original_capture = sdk.capture_single_data
            
            def failing_capture():
                raise RuntimeError("Simulated capture failure")
            
            sdk.capture_single_data = failing_capture
            
            # This should handle the exception gracefully
            sdk.start_continuous_capture(interval=0.1, duration=0.5)
            time.sleep(0.6)  # Let it run and fail
            
            if sdk.is_running:
                self.log_issue("HIGH", "Exception Safety",
                              "Continuous capture still running after repeated failures")
            
            sdk.stop_continuous_capture()
            
        except Exception as e:
            self.log_issue("MEDIUM", "Exception Safety",
                          f"Exception safety test failed: {e}")
        finally:
            sdk.cleanup()
    
    def analyze_timing_issues(self):
        """Analyze potential timing and synchronization issues"""
        print("\n=== Analyzing Timing Issues ===")
        
        import time
        
        # Test rapid start/stop operations
        sdk = JetsonSDK(output_dir="timing_test")
        
        for i in range(5):
            sdk.start_continuous_capture(interval=0.01, duration=0.1)
            time.sleep(0.02)  # Very short duration
            sdk.stop_continuous_capture()
            
            if sdk.is_running:
                self.log_issue("HIGH", "Timing Issues",
                              f"SDK still running after stop command (iteration {i})")
        
        sdk.cleanup()
    
    def run_all_analyses(self):
        """Run all advanced bug detection analyses"""
        print("Starting Advanced Bug Detection Analysis...")
        print("=" * 60)
        
        analyses = [
            self.analyze_state_management,
            self.analyze_resource_leaks,
            self.analyze_thread_safety_deep,
            self.analyze_error_handling_logic,
            self.analyze_data_validation,
            self.analyze_memory_usage_patterns,
            self.analyze_race_conditions_advanced,
            self.analyze_code_quality_issues,
            self.analyze_exception_safety,
            self.analyze_timing_issues,
        ]
        
        for analysis in analyses:
            try:
                analysis()
            except Exception as e:
                self.log_issue("CRITICAL", "Analysis Error",
                              f"Analysis {analysis.__name__} failed: {e}")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive bug report"""
        print("\n" + "=" * 60)
        print("ADVANCED BUG DETECTION REPORT")
        print("=" * 60)
        
        if not self.issues and not self.warnings:
            print("✅ NO CRITICAL ISSUES DETECTED!")
            print("The SDK passed advanced bug detection analysis.")
        else:
            if self.issues:
                print(f"🚨 CRITICAL ISSUES: {len(self.issues)}")
                for issue in self.issues:
                    print(f"  [{issue['severity']}] {issue['category']}: {issue['description']}")
                    if issue['file']:
                        print(f"      Location: {issue['file']}:{issue['line']}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
                categories = defaultdict(list)
                for warning in self.warnings:
                    categories[warning['category']].append(warning)
                
                for category, warns in categories.items():
                    print(f"\n  {category} ({len(warns)} issues):")
                    for warn in warns[:3]:  # Show first 3 of each category
                        print(f"    - {warn['description']}")
                        if warn['file']:
                            print(f"      {warn['file']}:{warn['line']}")
                    if len(warns) > 3:
                        print(f"    ... and {len(warns) - 3} more")
        
        print("\n" + "=" * 60)
        
        return {
            "critical_issues": len([i for i in self.issues if i['severity'] == 'CRITICAL']),
            "high_issues": len([i for i in self.issues if i['severity'] == 'HIGH']),
            "medium_issues": len([i for i in self.issues + self.warnings if i['severity'] == 'MEDIUM']),
            "low_issues": len([i for i in self.issues + self.warnings if i['severity'] == 'LOW']),
            "total_issues": len(self.issues),
            "total_warnings": len(self.warnings)
        }


def main():
    """Main function"""
    detector = AdvancedBugDetector()
    summary = detector.run_all_analyses()
    
    # Exit with appropriate code
    if summary['critical_issues'] > 0:
        sys.exit(2)
    elif summary['high_issues'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()