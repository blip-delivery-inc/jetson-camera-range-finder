# Jetson Orin Integration SDK

A modular Python SDK for the NVIDIA Jetson Orin platform that provides easy-to-use interfaces for camera and LIDAR data acquisition. This SDK serves as a foundation for robotics and AI development projects.

## Features

- **Camera Integration**: Support for USB, CSI, and IP cameras with plug-and-play detection
- **LIDAR Integration**: Support for USB, Serial, and Ethernet LIDAR devices
- **Modular Design**: Clean, well-documented code with separate modules for different hardware types
- **Error Handling**: Robust error handling for hardware detection and data acquisition
- **Data Logging**: Comprehensive logging and data storage capabilities
- **Easy Configuration**: Simple configuration for different hardware setups

## Platform Requirements

- **Device**: NVIDIA Jetson Orin (rev1)
- **CPU**: ARMv8
- **GPU**: NVIDIA Tegra Orin
- **RAM**: 7.4 GB
- **Storage**: 250 GB
- **OS**: JetPack (Ubuntu 64-bit)
- **Python**: 3.x

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd jetson-camera-range-finder
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python camera.py
python lidar.py
```

## Hardware Setup

### Cameras

The SDK supports various camera types:

- **USB Webcams**: Automatically detected and configured
- **CSI Cameras**: Jetson-specific camera interfaces
- **IP Cameras**: Network-based cameras

### LIDAR Devices

Supported LIDAR connection types:

- **USB LIDARs**: Common USB-to-Serial LIDAR devices
- **Serial LIDARs**: Direct serial connection
- **Ethernet LIDARs**: Network-based LIDAR devices

## Usage

### Basic Usage

Run the main application to test hardware detection and data capture:

```bash
python main.py
```

This will:
1. Detect all connected cameras and LIDAR devices
2. Connect to available hardware
3. Perform data capture and save results
4. Generate logs and output files

### Programmatic Usage

#### Camera Integration

```python
from camera import CameraManager, SimpleCamera

# Simple camera usage
camera = SimpleCamera()
if camera.connect():
    frame = camera.capture()
    if frame is not None:
        print(f"Captured frame: {frame.shape}")
    camera.disconnect()

# Advanced camera management
manager = CameraManager()
cameras = manager.detect_cameras()
for camera_info in cameras:
    if manager.connect_camera(camera_info['id'], camera_info):
        frame = manager.capture_frame(camera_info['id'])
        if frame is not None:
            manager.save_frame(camera_info['id'], 'capture.jpg')
        manager.disconnect_camera(camera_info['id'])
```

#### LIDAR Integration

```python
from lidar import LIDARManager, SimpleLIDAR, LIDARData

# Simple LIDAR usage
lidar = SimpleLIDAR()
if lidar.connect():
    distance = lidar.read_distance()
    if distance is not None:
        print(f"Distance: {distance:.3f} meters")
    lidar.disconnect()

# Advanced LIDAR management
manager = LIDARManager()
lidars = manager.detect_lidars()
for lidar_info in lidars:
    if manager.connect_lidar(lidar_info['id'], lidar_info):
        data = manager.read_data(lidar_info['id'])
        if data is not None:
            print(f"LIDAR data: {data}")
        manager.disconnect_lidar(lidar_info['id'])
```

#### Integrated SDK Usage

```python
from main import JetsonOrinSDK

# Initialize SDK
sdk = JetsonOrinSDK(output_dir="my_data")

# Detect hardware
hardware_info = sdk.detect_hardware()

# Connect to hardware
if sdk.connect_hardware(hardware_info):
    # Perform data capture
    summary = sdk.capture_data(duration=10.0, interval=1.0)
    print(f"Capture summary: {summary}")

# Cleanup
sdk.cleanup()
```

## Configuration

### Camera Configuration

Camera settings can be modified in the `CameraManager` class:

```python
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
    }
}
```

### LIDAR Configuration

LIDAR settings can be modified in the `LIDARManager` class:

```python
lidar_configs = {
    'serial': {
        'baudrate': 115200,
        'timeout': 1,
        'bytesize': serial.EIGHTBITS,
        'parity': serial.PARITY_NONE,
        'stopbits': serial.STOPBITS_ONE
    },
    'ethernet': {
        'host': '192.168.1.100',
        'port': 2111,
        'timeout': 5
    }
}
```

## Output Structure

The SDK generates the following output structure:

```
output/
├── hardware_detection.json    # Hardware detection results
├── capture_summary.json       # Data capture summary
├── jetson_sdk.log            # Application logs
├── camera_*.jpg              # Captured camera frames
└── simple_camera_*.jpg       # Simple camera captures
```

### Log Files

- `jetson_sdk.log`: Comprehensive application logs
- `hardware_detection.json`: JSON file containing detected hardware information
- `capture_summary.json`: JSON file containing data capture statistics

## Troubleshooting

### Common Issues

1. **No cameras detected**
   - Ensure cameras are properly connected
   - Check USB permissions: `sudo usermod -a -G video $USER`
   - Verify camera drivers are installed

2. **No LIDAR devices detected**
   - Check device permissions: `sudo usermod -a -G dialout $USER`
   - Verify LIDAR is powered and connected
   - Check device paths in `/dev/ttyUSB*` or `/dev/ttyACM*`

3. **Permission errors**
   - Add user to required groups:
     ```bash
     sudo usermod -a -G video,dialout $USER
     ```
   - Log out and log back in for changes to take effect

4. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

### Individual Module Testing

Test camera functionality:
```bash
python camera.py
```

Test LIDAR functionality:
```bash
python lidar.py
```

### Full System Testing

Run the complete SDK test:
```bash
python main.py
```

## Extensions and Customization

### Adding New Camera Types

1. Extend the `CameraManager` class
2. Add detection logic in `detect_cameras()`
3. Implement connection handling in `connect_camera()`

### Adding New LIDAR Types

1. Extend the `LIDARManager` class
2. Add detection logic in `detect_lidars()`
3. Implement data parsing in `_read_serial_data()` or `_read_ethernet_data()`

### ROS2 Integration

The SDK can be extended for ROS2 integration:

```python
import rclpy
from sensor_msgs.msg import Image, LaserScan

# Publish camera data
image_pub = node.create_publisher(Image, 'camera/image', 10)
# Publish LIDAR data
lidar_pub = node.create_publisher(LaserScan, 'lidar/scan', 10)
```

### Web Server Integration

Add real-time data publishing:

```python
from flask import Flask, jsonify
import cv2

app = Flask(__name__)

@app.route('/camera/current')
def get_current_image():
    # Capture and return current camera frame
    pass

@app.route('/lidar/current')
def get_current_lidar():
    # Return current LIDAR data
    pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `jetson_sdk.log`
3. Create an issue with detailed error information

## Changelog

### Version 1.0.0
- Initial release
- Camera and LIDAR integration
- Hardware detection and management
- Data capture and logging
- Modular architecture