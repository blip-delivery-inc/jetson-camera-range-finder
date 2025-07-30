# Jetson Edge SDK

A simple and powerful SDK for camera and laser range finder operations on NVIDIA Jetson Nano Orin. This SDK provides a unified interface for capturing camera frames and range finder data, making it easy to build edge computing applications for robotics, autonomous vehicles, and IoT projects.

## 🚀 Features

- **Simple API**: Easy-to-use interface with just a few lines of code
- **Dual Camera Support**: Works with both CSI and USB cameras
- **Range Finder Integration**: Supports common LIDAR sensors via serial communication
- **Real-time Processing**: Threaded architecture for continuous data capture
- **Flexible Configuration**: JSON-based configuration management
- **Rich Examples**: Multiple example applications included
- **Production Ready**: Proper error handling and resource management

## 📋 Requirements

### Hardware
- NVIDIA Jetson Nano Orin
- Camera (CSI or USB)
- Laser Range Finder (LIDAR) with serial interface
- USB-to-Serial adapter (if needed)

### Software
- Ubuntu 18.04+ (JetPack)
- Python 3.7+
- OpenCV 4.5+
- GStreamer (for CSI camera support)

## 🛠 Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/your-org/jetson-edge-sdk.git
cd jetson-edge-sdk

# Install dependencies
pip install -r requirements.txt

# Install the SDK
pip install -e .
```

### System Dependencies (Jetson-specific)
```bash
# Install GStreamer for CSI camera support
sudo apt-get update
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad

# For serial communication (if not already installed)
sudo apt-get install python3-serial

# Optional: Jetson system monitoring
pip install jetson-stats
```

## 🏗 Architecture

The SDK follows a modular architecture with clear separation of concerns:

```
jetson_edge_sdk/
├── core/
│   ├── sdk.py           # Main SDK orchestrator
│   ├── camera.py        # Camera management
│   ├── range_finder.py  # Range finder management
│   └── config.py        # Configuration management
├── examples/            # Example applications
└── config.json         # Default configuration
```

### Core Components

#### 1. **JetsonEdgeSDK** (`core/sdk.py`)
- **Purpose**: Main orchestrator class that manages all components
- **Responsibilities**: 
  - Initialize and coordinate camera and range finder
  - Provide unified API for data access
  - Handle system lifecycle (start/stop/cleanup)
- **Key Methods**: `initialize()`, `start()`, `stop()`, `get_camera_frame()`, `get_range_scan()`

#### 2. **CameraManager** (`core/camera.py`)
- **Purpose**: Handles all camera operations
- **Features**:
  - CSI camera support with GStreamer pipeline
  - USB camera support with OpenCV
  - Threaded capture for real-time performance
  - Frame callbacks for processing
- **Key Methods**: `initialize()`, `start_capture()`, `get_frame()`, `save_frame()`

#### 3. **RangeFinderManager** (`core/range_finder.py`)
- **Purpose**: Manages laser range finder communication
- **Features**:
  - Serial communication with LIDAR sensors
  - Threaded scanning for continuous data
  - Protocol parsing (currently supports RPLidar format)
  - Obstacle detection and mapping
- **Key Methods**: `initialize()`, `start_scan()`, `get_latest_scan()`, `get_distance_at_angle()`

#### 4. **Config** (`core/config.py`)
- **Purpose**: Configuration management system
- **Features**:
  - JSON-based configuration
  - Default settings with override capability
  - Type-safe configuration classes
  - Runtime configuration updates

### Data Flow Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Camera    │───▶│  SDK Core    │◀───│ Range Finder│
│  Hardware   │    │              │    │  Hardware   │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Application  │
                   │   Layer      │
                   └──────────────┘
```

1. **Hardware Layer**: Physical sensors (camera + LIDAR)
2. **SDK Core**: Abstraction and data management
3. **Application Layer**: User applications and examples

## 🚀 Quick Start

### Basic Usage

```python
from jetson_edge_sdk import JetsonEdgeSDK

# Initialize SDK
sdk = JetsonEdgeSDK()

# Initialize hardware
sdk.initialize(use_csi_camera=True)  # or False for USB camera

# Start operations
sdk.start()

# Get data
frame = sdk.get_camera_frame()      # Get latest camera frame
scan = sdk.get_range_scan()         # Get latest LIDAR scan
distance = sdk.get_distance_at_angle(0)  # Get distance at 0° (front)

# Save frame
sdk.save_camera_frame("capture.jpg")

# Clean shutdown
sdk.stop()
sdk.release()
```

### Using Context Manager (Recommended)

```python
from jetson_edge_sdk import JetsonEdgeSDK

with JetsonEdgeSDK() as sdk:
    if sdk.initialize() and sdk.start():
        # Wait for data to be available
        if sdk.wait_for_data(timeout=5.0):
            frame = sdk.get_camera_frame()
            scan = sdk.get_range_scan()
            
            # Process your data here
            print(f"Frame shape: {frame.shape}")
            print(f"Scan readings: {len(scan.readings)}")
```

### Real-time Processing with Callbacks

```python
from jetson_edge_sdk import JetsonEdgeSDK

def process_frame(frame):
    """Process each camera frame"""
    print(f"Processing frame: {frame.shape}")
    # Add your processing here

def process_scan(scan_data):
    """Process each LIDAR scan"""
    print(f"Processing scan: {len(scan_data.readings)} readings")
    # Add your processing here

with JetsonEdgeSDK() as sdk:
    sdk.initialize()
    sdk.start(
        frame_callback=process_frame,
        scan_callback=process_scan
    )
    
    # Let it run for 30 seconds
    time.sleep(30)
```

## ⚙️ Configuration

### Default Configuration (`config.json`)

```json
{
  "camera": {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "format": "MJPG",
    "device_id": 0,
    "flip_method": 0,
    "capture_width": 1920,
    "capture_height": 1080
  },
  "range_finder": {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "timeout": 1.0,
    "max_range": 100.0,
    "min_range": 0.1,
    "scan_angle": 270.0
  },
  "data_output_dir": "./data",
  "log_level": "INFO",
  "enable_camera": true,
  "enable_range_finder": true
}
```

### Configuration Options

#### Camera Settings
- `width/height`: Output resolution
- `fps`: Frames per second
- `format`: Video format ("MJPG" or "YUYV")
- `device_id`: Camera device ID (0 for first camera)
- `flip_method`: Image rotation for CSI cameras (0-3)

#### Range Finder Settings
- `port`: Serial port path (e.g., "/dev/ttyUSB0")
- `baudrate`: Serial communication speed
- `timeout`: Read timeout in seconds
- `max_range/min_range`: Distance filtering limits
- `scan_angle`: Scanner field of view

#### System Settings
- `data_output_dir`: Directory for saved files
- `log_level`: Logging verbosity ("DEBUG", "INFO", "WARNING", "ERROR")
- `enable_camera/enable_range_finder`: Enable/disable components

## 📖 Examples

The SDK includes several example applications:

### 1. Basic Usage (`examples/basic_usage.py`)
Simple data capture and display
```bash
python examples/basic_usage.py
```

### 2. Advanced Callbacks (`examples/advanced_callbacks.py`)
Real-time processing with callbacks
```bash
python examples/advanced_callbacks.py
```

### 3. Obstacle Detection (`examples/obstacle_detection.py`)
Combined camera and LIDAR obstacle detection
```bash
python examples/obstacle_detection.py
```

### Command Line Tools
After installation, you can use these commands:
```bash
jetson-edge-basic      # Run basic example
jetson-edge-callbacks  # Run callback example
jetson-edge-obstacles  # Run obstacle detection
```

## 🔧 Hardware Setup

### Camera Connection
- **CSI Camera**: Connect to CSI connector on Jetson
- **USB Camera**: Connect to USB port

### Range Finder Connection
1. Connect LIDAR to USB-to-Serial adapter
2. Connect adapter to Jetson USB port
3. Check device path: `ls /dev/ttyUSB*`
4. Update `config.json` with correct port

### Permissions
```bash
# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER
# Logout and login again
```

## 🐛 Troubleshooting

### Common Issues

#### Camera Not Found
```bash
# Check available cameras
ls /dev/video*

# For CSI camera, check GStreamer
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink
```

#### Range Finder Connection
```bash
# Check serial ports
ls /dev/ttyUSB*
ls /dev/ttyACM*

# Test serial communication
sudo minicom -D /dev/ttyUSB0 -b 115200
```

#### Permission Denied
```bash
# Fix serial port permissions
sudo chmod 666 /dev/ttyUSB0

# Or add user to dialout group (permanent)
sudo usermod -a -G dialout $USER
```

#### GStreamer Issues (CSI Camera)
```bash
# Install missing GStreamer plugins
sudo apt-get install gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly

# Check GStreamer installation
gst-inspect-1.0 nvarguscamerasrc
```

## 📊 Performance Tips

### Optimization Recommendations

1. **Use CSI Camera**: Better performance than USB for high-resolution capture
2. **Adjust Resolution**: Lower resolution = higher FPS
3. **Enable Hardware Acceleration**: Use Jetson's GPU for processing
4. **Optimize Threading**: Use callbacks for real-time processing
5. **Monitor System Resources**: Use `jtop` to monitor CPU/GPU usage

### System Monitoring
```bash
# Install jetson-stats
pip install jetson-stats

# Monitor system performance
jtop
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black jetson_edge_sdk/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/jetson-edge-sdk/issues)
- **Documentation**: [Project Wiki](https://github.com/your-org/jetson-edge-sdk/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/jetson-edge-sdk/discussions)

## 🙏 Acknowledgments

- NVIDIA for the Jetson platform
- OpenCV community for computer vision tools
- RPLidar community for LIDAR protocols

---

**Made with ❤️ for the Jetson community**