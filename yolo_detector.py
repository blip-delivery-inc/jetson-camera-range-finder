#!/usr/bin/env python3
"""
YOLO Object Detection Module for Jetson Orin Integration SDK

This module provides YOLO-based object detection capabilities that integrate
seamlessly with the existing camera system. It supports real-time object
detection, tracking, and annotation on camera feeds.

Features:
- YOLOv8 object detection using ultralytics
- Real-time inference on camera feeds
- Configurable confidence thresholds
- Object tracking and counting
- Bounding box visualization
- Detection logging and statistics

Author: Jetson Orin Integration SDK
Platform: NVIDIA Jetson Orin (JetPack Ubuntu 64-bit)
"""

import os
import cv2
import numpy as np
import logging
import time
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import json
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("ultralytics not available. Install with: pip install ultralytics")

logger = logging.getLogger(__name__)


class YOLOError(Exception):
    """Custom exception for YOLO-related errors"""
    pass


class YOLODetector:
    """
    YOLO Object Detection class for real-time inference
    """
    
    # COCO class names (80 classes)
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    def __init__(self, 
                 model_path: str = "yolov8n.pt",
                 confidence_threshold: float = 0.5,
                 iou_threshold: float = 0.45,
                 device: str = "auto"):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model file (will download if not exists)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on ('cpu', 'cuda', 'auto')
        """
        if not YOLO_AVAILABLE:
            raise YOLOError("ultralytics package not available. Install with: pip install ultralytics")
        
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        self.is_initialized = False
        
        # Detection statistics
        self.detection_count = 0
        self.total_inference_time = 0.0
        self.detection_history = []
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the YOLO model"""
        try:
            logger.info(f"Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)
            
            # Set device
            if self.device == "auto":
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            logger.info(f"YOLO model loaded successfully on device: {self.device}")
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {e}")
            raise YOLOError(f"Model initialization failed: {e}")
    
    def detect(self, image: np.ndarray, 
               annotate: bool = True,
               save_results: bool = False,
               output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform object detection on an image
        
        Args:
            image: Input image as numpy array (BGR format)
            annotate: Whether to draw bounding boxes on image
            save_results: Whether to save detection results
            output_path: Path to save annotated image
        
        Returns:
            Dictionary containing detection results
        """
        if not self.is_initialized:
            raise YOLOError("YOLO model not initialized")
        
        if image is None or image.size == 0:
            raise YOLOError("Invalid input image")
        
        start_time = time.time()
        
        try:
            # Run inference
            results = self.model(image, 
                               conf=self.confidence_threshold,
                               iou=self.iou_threshold,
                               device=self.device,
                               verbose=False)
            
            inference_time = time.time() - start_time
            self.total_inference_time += inference_time
            self.detection_count += 1
            
            # Process results
            detections = self._process_results(results[0], image.shape)
            
            # Create annotated image if requested
            annotated_image = image.copy()
            if annotate:
                annotated_image = self._annotate_image(image, detections)
            
            # Save results if requested
            if save_results and output_path:
                self._save_detection_results(detections, output_path, annotated_image)
            
            # Update detection history
            detection_result = {
                'timestamp': datetime.now().isoformat(),
                'inference_time': inference_time,
                'detections': detections,
                'image_shape': image.shape
            }
            
            self.detection_history.append(detection_result)
            
            # Keep only last 100 detections in memory
            if len(self.detection_history) > 100:
                self.detection_history.pop(0)
            
            return {
                'detections': detections,
                'annotated_image': annotated_image,
                'inference_time': inference_time,
                'detection_count': len(detections)
            }
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            raise YOLOError(f"Detection failed: {e}")
    
    def _process_results(self, result, image_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """Process YOLO detection results"""
        detections = []
        
        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
            confidences = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            
            for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
                x1, y1, x2, y2 = box
                
                detection = {
                    'id': i,
                    'class_id': int(cls_id),
                    'class_name': self.COCO_CLASSES[cls_id] if cls_id < len(self.COCO_CLASSES) else f'class_{cls_id}',
                    'confidence': float(conf),
                    'bbox': {
                        'x1': int(x1),
                        'y1': int(y1),
                        'x2': int(x2),
                        'y2': int(y2),
                        'width': int(x2 - x1),
                        'height': int(y2 - y1),
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    }
                }
                
                detections.append(detection)
        
        return detections
    
    def _annotate_image(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Draw bounding boxes and labels on image"""
        annotated = image.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(annotated, 
                         (bbox['x1'], bbox['y1']), 
                         (bbox['x2'], bbox['y2']), 
                         (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Draw label background
            cv2.rectangle(annotated,
                         (bbox['x1'], bbox['y1'] - label_size[1] - 10),
                         (bbox['x1'] + label_size[0], bbox['y1']),
                         (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(annotated, label,
                       (bbox['x1'], bbox['y1'] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated
    
    def _save_detection_results(self, detections: List[Dict[str, Any]], 
                              output_path: str, annotated_image: np.ndarray):
        """Save detection results to files"""
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save annotated image
            image_path = output_path.replace('.json', '_annotated.jpg')
            cv2.imwrite(image_path, annotated_image)
            
            # Save detection data
            detection_data = {
                'timestamp': datetime.now().isoformat(),
                'detections': detections,
                'detection_count': len(detections),
                'model_info': {
                    'model_path': self.model_path,
                    'confidence_threshold': self.confidence_threshold,
                    'iou_threshold': self.iou_threshold
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(detection_data, f, indent=2)
            
            logger.info(f"Detection results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save detection results: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        avg_inference_time = (self.total_inference_time / self.detection_count 
                             if self.detection_count > 0 else 0)
        
        return {
            'total_detections': self.detection_count,
            'total_inference_time': self.total_inference_time,
            'average_inference_time': avg_inference_time,
            'fps': 1.0 / avg_inference_time if avg_inference_time > 0 else 0,
            'model_info': {
                'model_path': self.model_path,
                'confidence_threshold': self.confidence_threshold,
                'iou_threshold': self.iou_threshold,
                'device': self.device
            }
        }
    
    def reset_statistics(self):
        """Reset detection statistics"""
        self.detection_count = 0
        self.total_inference_time = 0.0
        self.detection_history.clear()
        logger.info("Detection statistics reset")
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Confidence threshold updated to {threshold}")
        else:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
    
    def set_iou_threshold(self, threshold: float):
        """Update IoU threshold"""
        if 0.0 <= threshold <= 1.0:
            self.iou_threshold = threshold
            logger.info(f"IoU threshold updated to {threshold}")
        else:
            raise ValueError("IoU threshold must be between 0.0 and 1.0")
    
    def filter_detections_by_class(self, detections: List[Dict[str, Any]], 
                                  target_classes: List[str]) -> List[Dict[str, Any]]:
        """Filter detections by class names"""
        return [det for det in detections if det['class_name'] in target_classes]
    
    def count_objects_by_class(self, detections: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count detected objects by class"""
        class_counts = {}
        for detection in detections:
            class_name = detection['class_name']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        return class_counts


def detect_objects_in_image(image_path: str, 
                          model_path: str = "yolov8n.pt",
                          confidence: float = 0.5,
                          save_results: bool = True,
                          output_dir: str = "detections") -> Dict[str, Any]:
    """
    Convenience function to detect objects in a single image
    
    Args:
        image_path: Path to input image
        model_path: Path to YOLO model
        confidence: Confidence threshold
        save_results: Whether to save results
        output_dir: Output directory for results
    
    Returns:
        Detection results dictionary
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Initialize detector
    detector = YOLODetector(model_path=model_path, confidence_threshold=confidence)
    
    # Perform detection
    output_path = None
    if save_results:
        os.makedirs(output_dir, exist_ok=True)
        basename = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{basename}_detection.json")
    
    results = detector.detect(image, annotate=True, save_results=save_results, 
                            output_path=output_path)
    
    return results


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize detector
        detector = YOLODetector()
        print("YOLO Detector initialized successfully!")
        print(f"Statistics: {detector.get_statistics()}")
        
    except Exception as e:
        print(f"Error: {e}")