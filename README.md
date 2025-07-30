# Jetson Nano Orin Edge SDK

A lightweight edge SDK for the Jetson Nano Orin platform designed to handle cameras and laser range finder data processing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Edge SDK Architecture                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Camera    │  │   Camera    │  │    Laser    │         │
│  │   Module    │  │   Module    │  │   Range     │         │
│  │             │  │             │  │   Finder    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Data Acquisition Layer                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ Camera      │  │ Camera      │  │ Laser       │     │ │
│  │  │ Driver      │  │ Driver      │  │ Driver      │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Processing Pipeline                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ Image       │  │ Data        │  │ Fusion      │     │ │
│  │  │ Processing  │  │ Synchroniz. │  │ Engine      │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Output Layer                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ Network     │  │ Local       │  │ Logging     │     │ │
│  │  │ Interface   │  │ Storage     │  │ System      │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Core Modules
- **Camera Module**: Handles multiple camera streams with configurable parameters
- **Laser Range Finder Module**: Processes distance measurements and point cloud data
- **Data Fusion Engine**: Combines camera and laser data for unified processing

### 2. Data Acquisition Layer
- **Camera Drivers**: Supports USB, CSI, and IP cameras
- **Laser Driver**: Interfaces with common laser range finder protocols (UART, USB)
- **Data Synchronization**: Ensures temporal alignment of multi-sensor data

### 3. Processing Pipeline
- **Image Processing**: Basic operations (resize, filter, format conversion)
- **Data Synchronization**: Timestamp-based alignment of sensor data
- **Fusion Engine**: Combines visual and distance data for enhanced perception

### 4. Output Layer
- **Network Interface**: REST API and WebSocket for remote access
- **Local Storage**: Efficient data logging and caching
- **Logging System**: Comprehensive logging for debugging and monitoring

## Key Features

- **Lightweight**: Minimal resource footprint optimized for Jetson Nano Orin
- **Modular**: Easy to extend and customize for specific use cases
- **Real-time**: Low-latency processing pipeline
- **Configurable**: JSON-based configuration for easy deployment
- **Robust**: Error handling and recovery mechanisms

## Hardware Requirements

- Jetson Nano Orin (4GB or 8GB)
- USB cameras or CSI cameras
- Laser range finder (UART/USB interface)
- MicroSD card (32GB+ recommended)

## Software Dependencies

- Ubuntu 20.04 LTS
- Python 3.8+
- OpenCV 4.5+
- NumPy
- PySerial
- Flask (for REST API)
- Jetson Inference (optional for AI processing)

## Directory Structure

```
jetson-edge-sdk/
├── src/
│   ├── core/           # Core SDK modules
│   ├── drivers/        # Hardware drivers
│   ├── processing/     # Data processing pipeline
│   ├── output/         # Output interfaces
│   └── utils/          # Utility functions
├── config/             # Configuration files
├── examples/           # Usage examples
├── tests/              # Unit tests
├── docs/               # Documentation
└── scripts/            # Setup and deployment scripts
```

## Quick Start

1. **Installation**:
   ```bash
   git clone <repository>
   cd jetson-edge-sdk
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your hardware settings
   ```

3. **Run**:
   ```bash
   python src/main.py
   ```

## API Endpoints

- `GET /api/status` - System status
- `GET /api/camera/{id}/frame` - Get camera frame
- `GET /api/laser/distance` - Get laser distance reading
- `GET /api/fusion/data` - Get fused sensor data
- `POST /api/config` - Update configuration

## Performance Metrics

- **Latency**: <50ms end-to-end processing
- **Throughput**: 30 FPS camera + 10Hz laser data
- **Memory Usage**: <512MB RAM
- **CPU Usage**: <30% on Jetson Nano Orin

## Development Guidelines

- Follow PEP 8 coding standards
- Add unit tests for new features
- Document all public APIs
- Use type hints for better code clarity
- Implement proper error handling

## License

MIT License - see LICENSE file for details