# Jetson Orin Integration SDK

A comprehensive SDK for integrating camera and LIDAR sensors on the NVIDIA Jetson Orin platform. This SDK provides easy-to-use interfaces for capturing images and retrieving range data, serving as a foundation for robotics and AI development.

## Platform Details

- **Device**: NVIDIA Jetson Orin (rev1)
- **CPU**: ARMv8
- **GPU**: NVIDIA Tegra Orin
- **RAM**: 7.4 GB
- **Storage**: 250 GB
- **OS**: JetPack (Ubuntu 64-bit)
- **Internet**: Connected

## Features

### Camera Support
- **USB Webcams**: Plug-and-play support for standard USB cameras
- **CSI Cameras**: Native support for Camera Serial Interface cameras using GStreamer
- **IP Cameras**: Network camera support with HTTP/RTSP protocols
- **Multiple Backends**: Automatic fallback between V4L2 and other OpenCV backends
- **Configurable Resolution**: Support for various resolutions up to 1920x1080
- **Frame Rate Control**: Adjustable FPS settings

### LIDAR Support
- **RPLidar Series**: Slamtec RPLidar A1, A2, A3 support
- **YDLidar Series**: YDLidar X2, X4 and compatible models
- **Hokuyo URG Series**: URG-04LX, URG-30LX with SCIP protocol
- **SICK TiM Series**: Network-enabled LIDAR support
- **Generic Serial**: Support for custom LIDAR protocols
- **Multiple Interfaces**: USB, Serial (UART/RS232), and Ethernet connections

### YOLO Object Detection
- **YOLOv8 Integration**: State-of-the-art object detection using Ultralytics YOLOv8
- **Real-time Inference**: Live object detection on camera feeds
- **80 COCO Classes**: Detection of common objects (person, car, dog, laptop, etc.)
- **Configurable Confidence**: Adjustable detection thresholds
- **Bounding Box Visualization**: Automatic annotation of detected objects
- **Performance Optimized**: GPU acceleration support (CUDA when available)
- **Detection Statistics**: Comprehensive performance metrics and logging
- **Multiple Model Support**: Support for different YOLO model sizes (nano, small, medium, large, extra-large)

### Key Capabilities
- **Hardware Auto-Detection**: Automatic discovery of connected cameras and LIDAR devices
- **Real-time Data Acquisition**: Continuous capture with configurable intervals
- **YOLO Object Detection**: Real-time object detection and classification using YOLOv8
- **Data Logging**: JSON-based logging with timestamps
- **Error Handling**: Robust error detection and recovery
- **Modular Design**: Clean, extensible architecture
- **Thread-Safe**: Multi-threaded data collection

## Installation

### Prerequisites

Ensure your Jetson Orin is running JetPack with Ubuntu 64-bit and has the following system packages:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y v4l-utils
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# For serial communication
sudo apt install -y python3-serial

# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER
```

### SDK Installation

1. **Clone or download the SDK**:
```bash
git clone <repository-url>
cd jetson-orin-sdk
```

2. **Install Python dependencies**:
```bash
# Basic installation
pip3 install -r requirements.txt

# For YOLO object detection (recommended)
pip3 install ultralytics torch torchvision
```

3. **Verify installation**:
```bash
python3 main.py --mode detect
```

## Quick Start

### Basic Usage

1. **Detect Available Hardware**:
```bash
python3 main.py --mode detect
```

2. **Run Full Demo**:
```bash
python3 main.py --mode demo --duration 30
```

3. **Capture Single Data Point**:
```bash
python3 main.py --mode single --camera-type usb --lidar-type generic_serial
```

4. **Continuous Data Capture**:
```bash
python3 main.py --mode continuous --duration 60 --interval 2.0
```

5. **YOLO Object Detection Demo**:
```bash
python3 main.py --mode yolo --duration 30 --yolo-confidence 0.5
```

6. **Single Capture with YOLO**:
```bash
python3 main.py --mode single --enable-yolo --yolo-model yolov8n.pt --yolo-confidence 0.6
```

### Python API Usage

```python
from camera import JetsonCamera, detect_cameras
from lidar import JetsonLidar, LidarType
from main import JetsonSDK

# Initialize SDK
sdk = JetsonSDK(output_dir="my_data")

# Detect hardware
hardware = sdk.detect_hardware()
print(f"Found cameras: {hardware['cameras']}")
print(f"Found LIDAR devices: {hardware['lidars']}")

# Setup camera
if sdk.setup_camera("usb", 0):
    print("Camera connected successfully")

# Setup LIDAR
if sdk.setup_lidar("generic_serial", "/dev/ttyUSB0"):
    print("LIDAR connected successfully")

# Capture data
data = sdk.capture_single_data()
print(f"Captured data: {data}")

# Cleanup
sdk.cleanup()
```

### YOLO Object Detection API

```python
from camera import JetsonCamera
from yolo_detector import YOLODetector, detect_objects_in_image
from main import JetsonSDK

# Method 1: Direct YOLO detector usage
detector = YOLODetector(confidence_threshold=0.5)
results = detect_objects_in_image("image.jpg", save_results=True)
print(f"Detected {results['detection_count']} objects")

# Method 2: Camera with YOLO integration
camera = JetsonCamera(camera_type="usb", camera_id=0, enable_yolo=True, yolo_confidence=0.6)
if camera.connect():
    success, annotated_frame, detection_results = camera.capture_frame_with_detection()
    if success and detection_results:
        for detection in detection_results['detections']:
            print(f"Found {detection['class_name']} with confidence {detection['confidence']:.2f}")

# Method 3: SDK with YOLO
sdk = JetsonSDK()
if sdk.setup_camera("usb", 0):
    sdk.enable_yolo_detection(confidence=0.5)
    result = sdk.capture_with_detection(save_results=True)
    print(f"Detection result: {result}")
    
    # Get performance statistics
    stats = sdk.get_yolo_statistics()
    print(f"YOLO FPS: {stats['fps']:.1f}")
```

## Configuration

### Camera Configuration

```python
# USB Camera
camera = JetsonCamera(
    camera_id=0,
    camera_type="usb",
    width=1920,
    height=1080,
    fps=30
)

# CSI Camera
camera = JetsonCamera(
    camera_id=0,
    camera_type="csi",
    width=1920,
    height=1080,
    fps=30
)

# IP Camera
camera = JetsonCamera(
    camera_type="ip",
    ip_url="http://192.168.1.100:8080/video"
)
```

### LIDAR Configuration

```python
# RPLidar
lidar = JetsonLidar(
    lidar_type=LidarType.RPLIDAR,
    port="/dev/ttyUSB0",
    baudrate=115200
)

# Hokuyo URG
lidar = JetsonLidar(
    lidar_type=LidarType.HOKUYO_URG,
    port="/dev/ttyACM0",
    baudrate=19200
)

# Network LIDAR
lidar = JetsonLidar(
    lidar_type=LidarType.SICK_TIM,
    ip_address="192.168.1.10",
    ip_port=2111
)
```

## Command Line Options

```bash
python3 main.py [OPTIONS]

Options:
  --mode {demo,detect,single,continuous}  Operation mode (default: demo)
  --duration FLOAT                        Duration in seconds (default: 30.0)
  --interval FLOAT                        Capture interval in seconds (default: 1.0)
  --camera-type {usb,csi,ip}             Camera type (default: usb)
  --camera-id INT                         Camera device ID (default: 0)
  --camera-ip TEXT                        IP camera URL
  --lidar-type {rplidar,ydlidar,hokuyo_urg,sick_tim,generic_serial,generic_udp}
                                          LIDAR type (default: generic_serial)
  --lidar-port TEXT                       LIDAR serial port (default: /dev/ttyUSB0)
  --lidar-baudrate INT                    LIDAR baudrate (default: 115200)
  --output-dir TEXT                       Output directory (default: data)
```

## Hardware Setup

### Camera Setup

1. **USB Cameras**:
   - Connect USB camera to any available USB port
   - Verify detection: `lsusb` and `v4l2-ctl --list-devices`

2. **CSI Cameras**:
   - Connect to CSI connector (usually labeled CAM0/CAM1)
   - Ensure proper ribbon cable connection
   - Verify with: `ls /dev/video*`

3. **IP Cameras**:
   - Ensure camera and Jetson are on same network
   - Test connectivity: `ping <camera-ip>`
   - Verify stream URL in browser

### LIDAR Setup

1. **USB LIDAR**:
   - Connect via USB cable
   - Check device: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
   - Verify permissions: `ls -l /dev/ttyUSB0`

2. **Serial LIDAR**:
   - Connect to UART pins on Jetson
   - Configure serial parameters (baudrate, parity, etc.)
   - Enable serial port: `sudo systemctl enable serial-getty@ttyTHS0.service`

3. **Network LIDAR**:
   - Connect via Ethernet
   - Configure network settings
   - Test connection: `telnet <lidar-ip> <port>`

## Troubleshooting

### Common Issues

1. **Camera Not Detected**:
   ```bash
   # Check USB devices
   lsusb
   
   # Check video devices
   v4l2-ctl --list-devices
   
   # Test camera directly
   gst-launch-1.0 v4l2src device=/dev/video0 ! xvimagesink
   ```

2. **LIDAR Connection Failed**:
   ```bash
   # Check serial devices
   ls /dev/tty*
   
   # Check permissions
   sudo chmod 666 /dev/ttyUSB0
   
   # Test serial communication
   sudo minicom -D /dev/ttyUSB0 -b 115200
   ```

3. **CSI Camera Issues**:
   ```bash
   # Check GStreamer plugins
   gst-inspect-1.0 nvarguscamerasrc
   
   # Test CSI camera
   gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! nvvidconv ! xvimagesink
   ```

4. **Permission Errors**:
   ```bash
   # Add user to required groups
   sudo usermod -a -G video,dialout $USER
   
   # Logout and login again
   ```

### Performance Optimization

1. **Camera Performance**:
   - Use appropriate resolution for your application
   - Consider using CSI cameras for better performance
   - Adjust frame rate based on processing capability

2. **LIDAR Performance**:
   - Use appropriate baudrate for your LIDAR model
   - Consider buffering for high-frequency data
   - Implement data filtering if needed

3. **System Performance**:
   - Monitor CPU/GPU usage with `htop` and `tegrastats`
   - Use NVIDIA GPU acceleration when available
   - Consider using separate threads for I/O operations

## API Reference

### JetsonCamera Class

```python
class JetsonCamera:
    def __init__(self, camera_id=0, camera_type="usb", ip_url=None, width=1920, height=1080, fps=30)
    def connect(self) -> bool
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]
    def capture_multiple_frames(self, count=5, delay=0.1) -> list
    def get_camera_info(self) -> Dict[str, Any]
    def save_frame(self, filename: str) -> bool
    def disconnect(self)
```

### JetsonLidar Class

```python
class JetsonLidar:
    def __init__(self, lidar_type=LidarType.GENERIC_SERIAL, port="/dev/ttyUSB0", baudrate=115200, ip_address=None, ip_port=2111, timeout=1.0)
    def connect(self) -> bool
    def start_scan(self, callback=None) -> bool
    def stop_scan(self)
    def get_single_measurement(self) -> Optional[LidarPoint]
    def get_device_info(self) -> Dict[str, Any]
    def disconnect(self)
```

### JetsonSDK Class

```python
class JetsonSDK:
    def __init__(self, output_dir="data")
    def detect_hardware(self) -> dict
    def setup_camera(self, camera_type="usb", camera_id=0, ip_url=None) -> bool
    def setup_lidar(self, lidar_type="generic_serial", port="/dev/ttyUSB0", baudrate=115200, ip_address=None) -> bool
    def capture_single_data(self) -> dict
    def start_continuous_capture(self, interval=1.0, duration=None)
    def stop_continuous_capture(self)
    def get_statistics(self) -> dict
    def run_demo(self, duration=30.0)
    def cleanup(self)
```

## Data Format

### Captured Data Structure

```json
{
  "timestamp": 1640995200.123,
  "datetime": "2021-12-31T12:00:00.123000",
  "camera": {
    "filename": "image_1640995200.jpg",
    "shape": [1080, 1920, 3],
    "success": true
  },
  "lidar": {
    "angle": 0.0,
    "distance": 1500.0,
    "quality": 255,
    "timestamp": 1640995200.124,
    "success": true
  },
  "errors": []
}
```

### Hardware Detection Format

```json
{
  "cameras": {
    "usb": [0, 1],
    "csi": [0]
  },
  "lidars": [
    {
      "port": "/dev/ttyUSB0",
      "description": "USB Serial Device",
      "hwid": "USB VID:PID=10C4:EA60",
      "type": "serial",
      "likely_type": "generic_serial"
    }
  ],
  "timestamp": "2021-12-31T12:00:00.000000"
}
```

## Extensions and Customization

### Adding New Camera Types

1. Extend the `JetsonCamera` class
2. Implement connection method in `_connect_<type>()`
3. Add detection logic in `detect_cameras()`

### Adding New LIDAR Types

1. Add new enum to `LidarType`
2. Implement initialization in `_init_<type>()`
3. Add data parsing in `_read_<type>_data()`

### Custom Data Processing

```python
# Custom scan callback
def my_scan_callback(scan_data):
    # Process LIDAR scan data
    for point in scan_data.points:
        print(f"Distance: {point.distance}mm at {point.angle}°")

# Custom camera processing
def process_frame(frame):
    # Apply custom image processing
    processed = cv2.GaussianBlur(frame, (5, 5), 0)
    return processed
```

## Testing

### Unit Tests

```bash
# Run camera tests
python3 -m pytest tests/test_camera.py

# Run LIDAR tests
python3 -m pytest tests/test_lidar.py

# Run integration tests
python3 -m pytest tests/test_integration.py
```

### Manual Testing

```bash
# Test camera detection
python3 camera.py

# Test LIDAR detection
python3 lidar.py

# Test full SDK
python3 main.py --mode demo --duration 10
```

## Support and Contributing

### Getting Help

1. Check the troubleshooting section
2. Review log files in the output directory
3. Use verbose logging: `export PYTHONPATH=.; python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- USB, CSI, and IP camera support
- RPLidar, YDLidar, Hokuyo, and generic LIDAR support
- Real-time data acquisition
- Hardware auto-detection
- JSON data logging
- Command-line interface

## Future Enhancements

- [ ] ROS2 integration
- [ ] Real-time visualization
- [ ] Docker containerization
- [ ] Multiple camera streams
- [ ] Advanced LIDAR filtering
- [ ] Web-based monitoring interface
- [x] Machine learning integration (YOLO object detection)
- [ ] Point cloud processing