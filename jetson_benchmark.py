#!/usr/bin/env python3
"""
Jetson Orin Integration SDK - Performance Benchmark Suite

This script provides comprehensive performance testing for the SDK on Jetson hardware:
- Camera capture performance (USB, CSI)
- LIDAR data acquisition rates
- Memory usage monitoring
- CPU/GPU utilization tracking
- Thermal monitoring
- Power consumption analysis

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import os
import sys
import time
import json
import logging
import threading
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import SDK modules
from camera import JetsonCamera, detect_cameras, CameraError
from lidar import JetsonLidar, detect_lidar_devices, LidarType, LidarError
from main import JetsonSDK

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JetsonBenchmark:
    """Performance benchmarking suite for Jetson SDK"""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        """Initialize benchmark suite"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "camera_benchmarks": {},
            "lidar_benchmarks": {},
            "integration_benchmarks": {},
            "resource_usage": {},
            "thermal_data": {},
            "power_data": {}
        }
        
        # Monitoring flags
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info(f"Benchmark suite initialized. Results will be saved to: {self.output_dir}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        logger.info("Collecting system information...")
        
        info = {
            "platform": "Unknown",
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": sys.version,
            "opencv_version": None,
            "jetpack_version": None,
            "cuda_version": None
        }
        
        # Check if running on Jetson
        try:
            if os.path.exists("/etc/nv_tegra_release"):
                with open("/etc/nv_tegra_release", "r") as f:
                    info["jetpack_version"] = f.read().strip()
                info["platform"] = "NVIDIA Jetson"
            elif os.path.exists("/sys/firmware/devicetree/base/model"):
                with open("/sys/firmware/devicetree/base/model", "r") as f:
                    model = f.read().strip()
                    if "Jetson" in model:
                        info["platform"] = model
        except Exception as e:
            logger.warning(f"Could not read Jetson info: {e}")
        
        # Get OpenCV version
        try:
            import cv2
            info["opencv_version"] = cv2.__version__
        except ImportError:
            pass
        
        # Get CUDA version
        try:
            result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "release" in line:
                        info["cuda_version"] = line.split("release")[1].split(",")[0].strip()
                        break
        except FileNotFoundError:
            pass
        
        self.results["system_info"] = info
        logger.info(f"System: {info['platform']}, CPU cores: {info['cpu_count']}, RAM: {info['memory_total_gb']}GB")
        return info
    
    def start_resource_monitoring(self):
        """Start system resource monitoring"""
        self.monitoring_active = True
        self.resource_data = []
        
        def monitor_resources():
            while self.monitoring_active:
                try:
                    # CPU and memory usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    # GPU usage (if available)
                    gpu_usage = self.get_gpu_usage()
                    
                    # Temperature (if available)
                    temps = self.get_temperatures()
                    
                    # Power consumption (if available)
                    power = self.get_power_usage()
                    
                    data = {
                        "timestamp": time.time(),
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_used_gb": round(memory.used / (1024**3), 2),
                        "gpu_usage": gpu_usage,
                        "temperatures": temps,
                        "power_watts": power
                    }
                    
                    self.resource_data.append(data)
                    
                except Exception as e:
                    logger.warning(f"Resource monitoring error: {e}")
                
                time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_resource_monitoring(self):
        """Stop system resource monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        if hasattr(self, 'resource_data') and self.resource_data:
            self.results["resource_usage"] = {
                "samples": len(self.resource_data),
                "avg_cpu_percent": sum(d["cpu_percent"] for d in self.resource_data) / len(self.resource_data),
                "max_cpu_percent": max(d["cpu_percent"] for d in self.resource_data),
                "avg_memory_percent": sum(d["memory_percent"] for d in self.resource_data) / len(self.resource_data),
                "max_memory_gb": max(d["memory_used_gb"] for d in self.resource_data),
                "raw_data": self.resource_data
            }
        
        logger.info("Resource monitoring stopped")
    
    def get_gpu_usage(self) -> Optional[float]:
        """Get GPU usage percentage"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return None
    
    def get_temperatures(self) -> Dict[str, float]:
        """Get system temperatures"""
        temps = {}
        
        # Try Jetson thermal zones
        thermal_zones = ["/sys/class/thermal/thermal_zone0/temp",
                        "/sys/class/thermal/thermal_zone1/temp",
                        "/sys/class/thermal/thermal_zone2/temp"]
        
        for i, zone in enumerate(thermal_zones):
            try:
                if os.path.exists(zone):
                    with open(zone, "r") as f:
                        temp_millic = int(f.read().strip())
                        temps[f"thermal_zone_{i}"] = temp_millic / 1000.0
            except (FileNotFoundError, ValueError):
                continue
        
        # Try nvidia-smi for GPU temperature
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                temps["gpu"] = float(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return temps
    
    def get_power_usage(self) -> Optional[float]:
        """Get power consumption in watts"""
        try:
            # Try Jetson power monitoring
            if os.path.exists("/sys/bus/i2c/drivers/ina3221x/7-0040/iio:device0/in_power0_input"):
                with open("/sys/bus/i2c/drivers/ina3221x/7-0040/iio:device0/in_power0_input", "r") as f:
                    power_mw = int(f.read().strip())
                    return power_mw / 1000.0
        except (FileNotFoundError, ValueError):
            pass
        
        # Try nvidia-smi for GPU power
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                power_str = result.stdout.strip()
                if power_str != "N/A":
                    return float(power_str)
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None
    
    def benchmark_camera_detection(self) -> Dict[str, Any]:
        """Benchmark camera detection performance"""
        logger.info("Benchmarking camera detection...")
        
        start_time = time.time()
        cameras = detect_cameras()
        detection_time = time.time() - start_time
        
        result = {
            "detection_time_seconds": detection_time,
            "detected_cameras": cameras,
            "usb_camera_count": len(cameras.get("usb", [])),
            "csi_camera_count": len(cameras.get("csi", []))
        }
        
        logger.info(f"Camera detection completed in {detection_time:.3f}s")
        return result
    
    def benchmark_camera_capture(self, camera_type: str, camera_id: int, duration: float = 10.0) -> Dict[str, Any]:
        """Benchmark camera capture performance"""
        logger.info(f"Benchmarking {camera_type} camera {camera_id} capture...")
        
        try:
            camera = JetsonCamera(camera_type=camera_type, camera_id=camera_id)
            
            # Connection time
            start_time = time.time()
            if not camera.connect():
                return {"error": "Failed to connect to camera"}
            connection_time = time.time() - start_time
            
            # Capture performance test
            frames_captured = 0
            total_capture_time = 0
            failed_captures = 0
            
            test_start = time.time()
            while (time.time() - test_start) < duration:
                capture_start = time.time()
                ret, frame = camera.capture_frame()
                capture_time = time.time() - capture_start
                
                if ret and frame is not None:
                    frames_captured += 1
                    total_capture_time += capture_time
                else:
                    failed_captures += 1
                
                time.sleep(0.01)  # Small delay to prevent overwhelming
            
            camera.disconnect()
            
            # Calculate metrics
            actual_duration = time.time() - test_start
            avg_fps = frames_captured / actual_duration if actual_duration > 0 else 0
            avg_capture_time = total_capture_time / frames_captured if frames_captured > 0 else 0
            
            result = {
                "camera_type": camera_type,
                "camera_id": camera_id,
                "connection_time_seconds": connection_time,
                "test_duration_seconds": actual_duration,
                "frames_captured": frames_captured,
                "failed_captures": failed_captures,
                "average_fps": avg_fps,
                "average_capture_time_ms": avg_capture_time * 1000,
                "success_rate": frames_captured / (frames_captured + failed_captures) if (frames_captured + failed_captures) > 0 else 0
            }
            
            logger.info(f"{camera_type} camera benchmark: {avg_fps:.2f} FPS, {avg_capture_time*1000:.2f}ms avg capture time")
            return result
            
        except Exception as e:
            logger.error(f"Camera benchmark error: {e}")
            return {"error": str(e)}
    
    def benchmark_lidar_detection(self) -> Dict[str, Any]:
        """Benchmark LIDAR detection performance"""
        logger.info("Benchmarking LIDAR detection...")
        
        start_time = time.time()
        lidars = detect_lidar_devices()
        detection_time = time.time() - start_time
        
        result = {
            "detection_time_seconds": detection_time,
            "detected_lidars": lidars,
            "lidar_count": len(lidars)
        }
        
        logger.info(f"LIDAR detection completed in {detection_time:.3f}s")
        return result
    
    def benchmark_lidar_data(self, lidar_type: str, port: str, duration: float = 10.0) -> Dict[str, Any]:
        """Benchmark LIDAR data acquisition performance"""
        logger.info(f"Benchmarking {lidar_type} LIDAR data acquisition...")
        
        try:
            # Map string to enum
            lidar_type_map = {
                "rplidar": LidarType.RPLIDAR,
                "ydlidar": LidarType.YDLIDAR,
                "hokuyo_urg": LidarType.HOKUYO_URG,
                "sick_tim": LidarType.SICK_TIM,
                "generic_serial": LidarType.GENERIC_SERIAL,
                "generic_udp": LidarType.GENERIC_UDP
            }
            
            lidar_enum = lidar_type_map.get(lidar_type, LidarType.GENERIC_SERIAL)
            lidar = JetsonLidar(lidar_type=lidar_enum, port=port)
            
            # Connection time
            start_time = time.time()
            if not lidar.connect():
                return {"error": "Failed to connect to LIDAR"}
            connection_time = time.time() - start_time
            
            # Data acquisition test
            measurements_count = 0
            total_acquisition_time = 0
            failed_acquisitions = 0
            
            test_start = time.time()
            while (time.time() - test_start) < duration:
                acquisition_start = time.time()
                measurement = lidar.get_single_measurement()
                acquisition_time = time.time() - acquisition_start
                
                if measurement:
                    measurements_count += 1
                    total_acquisition_time += acquisition_time
                else:
                    failed_acquisitions += 1
                
                time.sleep(0.01)  # Small delay
            
            lidar.disconnect()
            
            # Calculate metrics
            actual_duration = time.time() - test_start
            avg_rate = measurements_count / actual_duration if actual_duration > 0 else 0
            avg_acquisition_time = total_acquisition_time / measurements_count if measurements_count > 0 else 0
            
            result = {
                "lidar_type": lidar_type,
                "port": port,
                "connection_time_seconds": connection_time,
                "test_duration_seconds": actual_duration,
                "measurements_count": measurements_count,
                "failed_acquisitions": failed_acquisitions,
                "average_rate_hz": avg_rate,
                "average_acquisition_time_ms": avg_acquisition_time * 1000,
                "success_rate": measurements_count / (measurements_count + failed_acquisitions) if (measurements_count + failed_acquisitions) > 0 else 0
            }
            
            logger.info(f"{lidar_type} LIDAR benchmark: {avg_rate:.2f} Hz, {avg_acquisition_time*1000:.2f}ms avg acquisition time")
            return result
            
        except Exception as e:
            logger.error(f"LIDAR benchmark error: {e}")
            return {"error": str(e)}
    
    def benchmark_integration(self, duration: float = 30.0) -> Dict[str, Any]:
        """Benchmark full SDK integration performance"""
        logger.info("Benchmarking SDK integration performance...")
        
        try:
            sdk = JetsonSDK(output_dir=str(self.output_dir / "integration_test"))
            
            # Hardware detection
            detection_start = time.time()
            hardware = sdk.detect_hardware()
            detection_time = time.time() - detection_start
            
            # Setup devices
            setup_times = {}
            
            # Setup camera if available
            camera_setup = False
            if hardware["cameras"]["usb"]:
                setup_start = time.time()
                camera_setup = sdk.setup_camera("usb", hardware["cameras"]["usb"][0])
                setup_times["camera"] = time.time() - setup_start
            elif hardware["cameras"]["csi"]:
                setup_start = time.time()
                camera_setup = sdk.setup_camera("csi", hardware["cameras"]["csi"][0])
                setup_times["camera"] = time.time() - setup_start
            
            # Setup LIDAR if available
            lidar_setup = False
            if hardware["lidars"]:
                device = hardware["lidars"][0]
                setup_start = time.time()
                lidar_setup = sdk.setup_lidar(
                    device.get("likely_type", "generic_serial"),
                    device["port"]
                )
                setup_times["lidar"] = time.time() - setup_start
            
            # Data capture performance
            capture_count = 0
            total_capture_time = 0
            errors = 0
            
            test_start = time.time()
            while (time.time() - test_start) < duration:
                capture_start = time.time()
                try:
                    data = sdk.capture_single_data()
                    capture_time = time.time() - capture_start
                    
                    capture_count += 1
                    total_capture_time += capture_time
                    
                    if data.get("errors"):
                        errors += len(data["errors"])
                    
                except Exception as e:
                    errors += 1
                    logger.warning(f"Capture error: {e}")
                
                time.sleep(0.1)  # 10 Hz capture rate
            
            sdk.cleanup()
            
            # Calculate metrics
            actual_duration = time.time() - test_start
            avg_capture_rate = capture_count / actual_duration if actual_duration > 0 else 0
            avg_capture_time = total_capture_time / capture_count if capture_count > 0 else 0
            
            result = {
                "detection_time_seconds": detection_time,
                "setup_times": setup_times,
                "camera_setup_success": camera_setup,
                "lidar_setup_success": lidar_setup,
                "test_duration_seconds": actual_duration,
                "capture_count": capture_count,
                "error_count": errors,
                "average_capture_rate_hz": avg_capture_rate,
                "average_capture_time_ms": avg_capture_time * 1000,
                "error_rate": errors / capture_count if capture_count > 0 else 0
            }
            
            logger.info(f"Integration benchmark: {avg_capture_rate:.2f} Hz capture rate, {errors} errors")
            return result
            
        except Exception as e:
            logger.error(f"Integration benchmark error: {e}")
            return {"error": str(e)}
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        logger.info("Starting full benchmark suite...")
        
        # Start resource monitoring
        self.start_resource_monitoring()
        
        try:
            # System information
            self.get_system_info()
            
            # Camera benchmarks
            camera_results = {}
            camera_results["detection"] = self.benchmark_camera_detection()
            
            # Test available cameras
            cameras = camera_results["detection"]["detected_cameras"]
            for camera_type in ["usb", "csi"]:
                if cameras.get(camera_type):
                    for camera_id in cameras[camera_type][:2]:  # Test first 2 cameras
                        key = f"{camera_type}_{camera_id}"
                        camera_results[key] = self.benchmark_camera_capture(camera_type, camera_id, 10.0)
            
            self.results["camera_benchmarks"] = camera_results
            
            # LIDAR benchmarks
            lidar_results = {}
            lidar_results["detection"] = self.benchmark_lidar_detection()
            
            # Test available LIDARs
            lidars = lidar_results["detection"]["detected_lidars"]
            for i, lidar in enumerate(lidars[:2]):  # Test first 2 LIDARs
                key = f"lidar_{i}"
                lidar_results[key] = self.benchmark_lidar_data(
                    lidar.get("likely_type", "generic_serial"),
                    lidar["port"],
                    10.0
                )
            
            self.results["lidar_benchmarks"] = lidar_results
            
            # Integration benchmark
            self.results["integration_benchmarks"] = self.benchmark_integration(30.0)
            
        finally:
            # Stop resource monitoring
            self.stop_resource_monitoring()
        
        # Save results
        results_file = self.output_dir / f"benchmark_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Benchmark completed. Results saved to: {results_file}")
        return self.results
    
    def generate_report(self) -> str:
        """Generate human-readable benchmark report"""
        report = []
        report.append("=" * 60)
        report.append("JETSON ORIN SDK PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {self.results['timestamp']}")
        report.append("")
        
        # System info
        sys_info = self.results["system_info"]
        report.append("SYSTEM INFORMATION:")
        report.append(f"  Platform: {sys_info.get('platform', 'Unknown')}")
        report.append(f"  CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
        report.append(f"  Total Memory: {sys_info.get('memory_total_gb', 'Unknown')} GB")
        report.append(f"  OpenCV Version: {sys_info.get('opencv_version', 'Unknown')}")
        report.append(f"  JetPack Version: {sys_info.get('jetpack_version', 'Unknown')}")
        report.append("")
        
        # Camera benchmarks
        cam_bench = self.results.get("camera_benchmarks", {})
        if cam_bench:
            report.append("CAMERA PERFORMANCE:")
            detection = cam_bench.get("detection", {})
            report.append(f"  Detection Time: {detection.get('detection_time_seconds', 0):.3f}s")
            report.append(f"  USB Cameras: {detection.get('usb_camera_count', 0)}")
            report.append(f"  CSI Cameras: {detection.get('csi_camera_count', 0)}")
            
            for key, result in cam_bench.items():
                if key != "detection" and "error" not in result:
                    report.append(f"  {key.upper()}:")
                    report.append(f"    Average FPS: {result.get('average_fps', 0):.2f}")
                    report.append(f"    Capture Time: {result.get('average_capture_time_ms', 0):.2f}ms")
                    report.append(f"    Success Rate: {result.get('success_rate', 0)*100:.1f}%")
            report.append("")
        
        # LIDAR benchmarks
        lidar_bench = self.results.get("lidar_benchmarks", {})
        if lidar_bench:
            report.append("LIDAR PERFORMANCE:")
            detection = lidar_bench.get("detection", {})
            report.append(f"  Detection Time: {detection.get('detection_time_seconds', 0):.3f}s")
            report.append(f"  LIDAR Devices: {detection.get('lidar_count', 0)}")
            
            for key, result in lidar_bench.items():
                if key != "detection" and "error" not in result:
                    report.append(f"  {key.upper()}:")
                    report.append(f"    Average Rate: {result.get('average_rate_hz', 0):.2f} Hz")
                    report.append(f"    Acquisition Time: {result.get('average_acquisition_time_ms', 0):.2f}ms")
                    report.append(f"    Success Rate: {result.get('success_rate', 0)*100:.1f}%")
            report.append("")
        
        # Integration benchmarks
        int_bench = self.results.get("integration_benchmarks", {})
        if int_bench and "error" not in int_bench:
            report.append("INTEGRATION PERFORMANCE:")
            report.append(f"  Hardware Detection: {int_bench.get('detection_time_seconds', 0):.3f}s")
            report.append(f"  Capture Rate: {int_bench.get('average_capture_rate_hz', 0):.2f} Hz")
            report.append(f"  Capture Time: {int_bench.get('average_capture_time_ms', 0):.2f}ms")
            report.append(f"  Error Rate: {int_bench.get('error_rate', 0)*100:.1f}%")
            report.append("")
        
        # Resource usage
        resource = self.results.get("resource_usage", {})
        if resource:
            report.append("RESOURCE USAGE:")
            report.append(f"  Average CPU: {resource.get('avg_cpu_percent', 0):.1f}%")
            report.append(f"  Peak CPU: {resource.get('max_cpu_percent', 0):.1f}%")
            report.append(f"  Average Memory: {resource.get('avg_memory_percent', 0):.1f}%")
            report.append(f"  Peak Memory: {resource.get('max_memory_gb', 0):.2f} GB")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main benchmark function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jetson Orin SDK Performance Benchmark")
    parser.add_argument("--output-dir", default="benchmark_results", help="Output directory")
    parser.add_argument("--duration", type=float, default=30.0, help="Test duration in seconds")
    parser.add_argument("--camera-only", action="store_true", help="Run camera benchmarks only")
    parser.add_argument("--lidar-only", action="store_true", help="Run LIDAR benchmarks only")
    parser.add_argument("--integration-only", action="store_true", help="Run integration benchmarks only")
    
    args = parser.parse_args()
    
    # Initialize benchmark suite
    benchmark = JetsonBenchmark(output_dir=args.output_dir)
    
    try:
        if args.camera_only:
            logger.info("Running camera benchmarks only...")
            benchmark.start_resource_monitoring()
            benchmark.get_system_info()
            benchmark.results["camera_benchmarks"] = {
                "detection": benchmark.benchmark_camera_detection()
            }
            benchmark.stop_resource_monitoring()
            
        elif args.lidar_only:
            logger.info("Running LIDAR benchmarks only...")
            benchmark.start_resource_monitoring()
            benchmark.get_system_info()
            benchmark.results["lidar_benchmarks"] = {
                "detection": benchmark.benchmark_lidar_detection()
            }
            benchmark.stop_resource_monitoring()
            
        elif args.integration_only:
            logger.info("Running integration benchmarks only...")
            benchmark.start_resource_monitoring()
            benchmark.get_system_info()
            benchmark.results["integration_benchmarks"] = benchmark.benchmark_integration(args.duration)
            benchmark.stop_resource_monitoring()
            
        else:
            # Run full benchmark suite
            results = benchmark.run_full_benchmark()
        
        # Generate and display report
        report = benchmark.generate_report()
        print("\n" + report)
        
        # Save report to file
        report_file = benchmark.output_dir / f"benchmark_report_{int(time.time())}.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        logger.info(f"Benchmark report saved to: {report_file}")
        
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")


if __name__ == "__main__":
    main()