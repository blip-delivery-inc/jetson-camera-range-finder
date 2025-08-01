#!/usr/bin/env python3
"""
YOLO Integration Test Script

This script tests the YOLO integration with the Jetson Orin Integration SDK.
It demonstrates:
- YOLO detector initialization
- Object detection on test images
- Camera integration with YOLO
- Performance statistics
- Error handling

Usage:
    python test_yolo_integration.py

Author: Jetson Orin Integration SDK
"""

import os
import sys
import cv2
import numpy as np
import logging
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')

try:
    from yolo_detector import YOLODetector, detect_objects_in_image
    from camera import JetsonCamera
    from main import JetsonSDK
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_images():
    """Create test images for YOLO detection"""
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Test image 1: Simple shapes
    img1 = np.zeros((480, 640, 3), dtype=np.uint8)
    img1.fill(100)
    cv2.rectangle(img1, (100, 100), (300, 300), (255, 0, 0), -1)
    cv2.circle(img1, (500, 150), 80, (0, 255, 0), -1)
    cv2.putText(img1, 'Geometric Shapes', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite(str(test_dir / "shapes.jpg"), img1)
    
    # Test image 2: More complex scene (still synthetic)
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 200
    # Draw some rectangular objects that might look like books, laptops, etc.
    cv2.rectangle(img2, (50, 200), (200, 350), (139, 69, 19), -1)  # Brown rectangle (book-like)
    cv2.rectangle(img2, (250, 180), (450, 320), (64, 64, 64), -1)  # Gray rectangle (laptop-like)
    cv2.rectangle(img2, (480, 100), (600, 200), (255, 255, 255), -1)  # White rectangle
    cv2.putText(img2, 'Object-like Shapes', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(str(test_dir / "objects.jpg"), img2)
    
    logger.info(f"Created test images in {test_dir}")
    return [str(test_dir / "shapes.jpg"), str(test_dir / "objects.jpg")]


def test_yolo_detector():
    """Test basic YOLO detector functionality"""
    logger.info("Testing YOLO Detector initialization...")
    
    try:
        # Initialize detector
        detector = YOLODetector(confidence_threshold=0.3)
        logger.info("✓ YOLO Detector initialized successfully")
        
        # Get initial statistics
        stats = detector.get_statistics()
        logger.info(f"Initial statistics: {stats}")
        
        return detector
        
    except Exception as e:
        logger.error(f"✗ YOLO Detector initialization failed: {e}")
        return None


def test_image_detection(detector, image_paths):
    """Test YOLO detection on images"""
    logger.info("Testing YOLO detection on images...")
    
    results = []
    
    for image_path in image_paths:
        logger.info(f"Processing {image_path}...")
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"✗ Could not load image: {image_path}")
                continue
            
            # Perform detection
            result = detector.detect(image, annotate=True, save_results=True, 
                                   output_path=f"detections/{Path(image_path).stem}_detection.json")
            
            logger.info(f"✓ Detection completed for {image_path}")
            logger.info(f"  - Objects detected: {result['detection_count']}")
            logger.info(f"  - Inference time: {result['inference_time']:.3f}s")
            
            if result['detections']:
                for det in result['detections']:
                    logger.info(f"    - {det['class_name']}: {det['confidence']:.2f}")
            
            results.append({
                'image': image_path,
                'detection_count': result['detection_count'],
                'inference_time': result['inference_time'],
                'detections': result['detections']
            })
            
        except Exception as e:
            logger.error(f"✗ Detection failed for {image_path}: {e}")
    
    return results


def test_camera_integration():
    """Test YOLO integration with camera system"""
    logger.info("Testing YOLO integration with camera system...")
    
    try:
        # Initialize camera with YOLO enabled
        camera = JetsonCamera(camera_type="usb", camera_id=0, enable_yolo=True, yolo_confidence=0.3)
        logger.info("✓ Camera with YOLO initialized")
        
        # Test YOLO methods
        yolo_stats = camera.get_yolo_statistics()
        if yolo_stats:
            logger.info(f"✓ YOLO statistics retrieved: {yolo_stats}")
        else:
            logger.warning("⚠ YOLO statistics not available")
        
        # Test confidence threshold setting
        camera.set_yolo_confidence(0.4)
        logger.info("✓ YOLO confidence threshold updated")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Camera integration test failed: {e}")
        return False


def test_sdk_integration():
    """Test YOLO integration with main SDK"""
    logger.info("Testing YOLO integration with main SDK...")
    
    try:
        # Initialize SDK
        sdk = JetsonSDK(output_dir="test_output")
        logger.info("✓ SDK initialized")
        
        # Test YOLO enabling
        success = sdk.enable_yolo_detection(confidence=0.3)
        if success:
            logger.info("✓ YOLO detection enabled in SDK")
        else:
            logger.warning("⚠ YOLO detection could not be enabled (no camera)")
        
        # Test YOLO statistics
        yolo_stats = sdk.get_yolo_statistics()
        logger.info(f"YOLO statistics from SDK: {yolo_stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ SDK integration test failed: {e}")
        return False


def test_convenience_function():
    """Test the convenience function for single image detection"""
    logger.info("Testing convenience function...")
    
    # Create a simple test image
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    img.fill(150)
    cv2.rectangle(img, (100, 100), (300, 200), (0, 255, 255), -1)
    test_path = "convenience_test.jpg"
    cv2.imwrite(test_path, img)
    
    try:
        results = detect_objects_in_image(
            test_path, 
            confidence=0.3, 
            save_results=True, 
            output_dir="convenience_output"
        )
        
        logger.info("✓ Convenience function test completed")
        logger.info(f"  - Detection count: {results['detection_count']}")
        logger.info(f"  - Inference time: {results['inference_time']:.3f}s")
        
        # Cleanup
        os.remove(test_path)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Convenience function test failed: {e}")
        return False


def run_performance_test(detector, num_iterations=10):
    """Run performance test"""
    logger.info(f"Running performance test ({num_iterations} iterations)...")
    
    # Create test image
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    times = []
    
    for i in range(num_iterations):
        try:
            result = detector.detect(test_img, annotate=False, save_results=False)
            times.append(result['inference_time'])
        except Exception as e:
            logger.error(f"Performance test iteration {i+1} failed: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        logger.info(f"✓ Performance test completed:")
        logger.info(f"  - Average inference time: {avg_time:.3f}s")
        logger.info(f"  - Min/Max time: {min_time:.3f}s / {max_time:.3f}s")
        logger.info(f"  - Estimated FPS: {fps:.1f}")
        
        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'fps': fps
        }
    
    return None


def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("YOLO Integration Test Suite")
    logger.info("=" * 60)
    
    if not IMPORTS_AVAILABLE:
        logger.error("Required modules not available. Please install dependencies.")
        return False
    
    # Create output directories
    Path("detections").mkdir(exist_ok=True)
    Path("test_output").mkdir(exist_ok=True)
    
    test_results = {
        'yolo_detector': False,
        'image_detection': False,
        'camera_integration': False,
        'sdk_integration': False,
        'convenience_function': False,
        'performance_test': None
    }
    
    # Test 1: YOLO Detector
    detector = test_yolo_detector()
    test_results['yolo_detector'] = detector is not None
    
    if detector:
        # Test 2: Image Detection
        logger.info("\n" + "-" * 40)
        test_images = create_test_images()
        detection_results = test_image_detection(detector, test_images)
        test_results['image_detection'] = len(detection_results) > 0
        
        # Test 3: Performance Test
        logger.info("\n" + "-" * 40)
        perf_results = run_performance_test(detector)
        test_results['performance_test'] = perf_results
    
    # Test 4: Camera Integration
    logger.info("\n" + "-" * 40)
    test_results['camera_integration'] = test_camera_integration()
    
    # Test 5: SDK Integration
    logger.info("\n" + "-" * 40)
    test_results['sdk_integration'] = test_sdk_integration()
    
    # Test 6: Convenience Function
    logger.info("\n" + "-" * 40)
    test_results['convenience_function'] = test_convenience_function()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results.items():
        if test_name == 'performance_test':
            continue
        total += 1
        if result:
            passed += 1
            logger.info(f"✓ {test_name.replace('_', ' ').title()}: PASSED")
        else:
            logger.info(f"✗ {test_name.replace('_', ' ').title()}: FAILED")
    
    if test_results['performance_test']:
        perf = test_results['performance_test']
        logger.info(f"📊 Performance: {perf['fps']:.1f} FPS avg")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! YOLO integration is working correctly.")
        return True
    else:
        logger.warning("⚠ Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)