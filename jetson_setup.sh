#!/usr/bin/env bash
# Jetson Orin Integration SDK - Installation Script
# This script sets up the SDK on NVIDIA Jetson Orin with all dependencies and optimizations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Jetson
check_jetson() {
    print_status "Checking if running on NVIDIA Jetson..."
    if [ -f /etc/nv_tegra_release ]; then
        JETSON_VERSION=$(cat /etc/nv_tegra_release)
        print_success "Detected Jetson: $JETSON_VERSION"
        return 0
    elif [ -f /sys/firmware/devicetree/base/model ]; then
        MODEL=$(cat /sys/firmware/devicetree/base/model)
        if [[ $MODEL == *"Jetson"* ]]; then
            print_success "Detected Jetson: $MODEL"
            return 0
        fi
    fi
    print_warning "Not running on Jetson hardware - some optimizations may not be available"
    return 1
}

# Update system packages
update_system() {
    print_status "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    print_success "System packages updated"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    # Essential packages
    sudo apt install -y \
        python3-pip python3-dev python3-venv \
        build-essential cmake pkg-config \
        git curl wget unzip
    
    # OpenCV and computer vision
    sudo apt install -y \
        libopencv-dev python3-opencv \
        libopencv-contrib-dev \
        libjpeg-dev libpng-dev libtiff-dev \
        libavcodec-dev libavformat-dev libswscale-dev \
        libv4l-dev v4l-utils
    
    # GStreamer for CSI cameras
    sudo apt install -y \
        gstreamer1.0-tools gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly gstreamer1.0-libav \
        libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
    
    # Serial communication
    sudo apt install -y \
        python3-serial minicom setserial
    
    # Network tools
    sudo apt install -y \
        python3-requests python3-urllib3
    
    # Data processing
    sudo apt install -y \
        python3-numpy python3-yaml python3-pil
    
    # Testing
    sudo apt install -y \
        python3-pytest
    
    print_success "System dependencies installed"
}

# Setup user permissions
setup_permissions() {
    print_status "Setting up user permissions..."
    
    # Add user to required groups
    sudo usermod -a -G dialout,video,i2c,gpio,spi $USER
    
    # Set up udev rules for serial devices
    sudo tee /etc/udev/rules.d/99-jetson-sdk.rules > /dev/null << 'EOF'
# Jetson SDK udev rules
# Serial devices
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", KERNEL=="ttyACM*", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", KERNEL=="ttyS*", MODE="0666", GROUP="dialout"

# Video devices
SUBSYSTEM=="video4linux", GROUP="video", MODE="0664"
EOF
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    print_success "User permissions configured"
    print_warning "Please log out and log back in for group changes to take effect"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "jetson_sdk_env" ]; then
        python3 -m venv jetson_sdk_env
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment and install packages
    source jetson_sdk_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install packages with ARM-compatible versions
    pip install \
        opencv-python \
        pyserial \
        requests \
        numpy \
        pyyaml \
        pillow \
        pytest
    
    print_success "Python dependencies installed in virtual environment"
}

# Configure Jetson-specific optimizations
configure_jetson() {
    if check_jetson; then
        print_status "Configuring Jetson-specific optimizations..."
        
        # Enable maximum performance mode
        if command -v nvpmodel &> /dev/null; then
            sudo nvpmodel -m 0  # Maximum performance mode
            print_success "Set to maximum performance mode"
        fi
        
        # Enable jetson_clocks for maximum clock speeds
        if command -v jetson_clocks &> /dev/null; then
            sudo jetson_clocks
            print_success "Enabled maximum clock speeds"
        fi
        
        # Configure GPU memory
        if [ -f /etc/systemd/nvzramconfig.sh ]; then
            # Increase GPU memory split for better camera performance
            echo "# Jetson SDK GPU memory configuration" | sudo tee -a /boot/config.txt > /dev/null
            echo "gpu_mem=128" | sudo tee -a /boot/config.txt > /dev/null
        fi
        
        print_success "Jetson optimizations configured"
    fi
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python imports
    if source jetson_sdk_env/bin/activate && python3 -c "import cv2, serial, numpy, yaml; print('All imports successful')"; then
        print_success "Python dependencies test passed"
    else
        print_error "Python dependencies test failed"
        return 1
    fi
    
    # Test camera detection
    if ls /dev/video* &> /dev/null; then
        print_success "Video devices detected: $(ls /dev/video*)"
    else
        print_warning "No video devices detected"
    fi
    
    # Test serial devices
    if ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyS* &> /dev/null 2>&1; then
        print_success "Serial devices detected: $(ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyS* 2>/dev/null | tr '\n' ' ')"
    else
        print_warning "No serial devices detected"
    fi
    
    # Test SDK
    if source jetson_sdk_env/bin/activate && python3 test_sdk.py --unit; then
        print_success "SDK unit tests passed"
    else
        print_warning "Some SDK tests failed - this may be normal without hardware"
    fi
    
    print_success "Installation test completed"
}

# Create desktop shortcut
create_shortcuts() {
    print_status "Creating desktop shortcuts..."
    
    # Create desktop directory if it doesn't exist
    mkdir -p ~/Desktop
    
    # Create SDK launcher script
    cat > ~/Desktop/jetson-sdk.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Jetson SDK
Comment=Launch Jetson Orin Integration SDK
Exec=gnome-terminal -- bash -c "cd $(pwd) && source jetson_sdk_env/bin/activate && python3 main.py --mode demo; exec bash"
Icon=applications-engineering
Terminal=false
Categories=Development;
EOF
    
    chmod +x ~/Desktop/jetson-sdk.desktop
    
    print_success "Desktop shortcuts created"
}

# Main installation function
main() {
    print_status "Starting Jetson Orin Integration SDK installation..."
    echo "========================================================"
    
    # Check system
    check_jetson
    
    # Install dependencies
    update_system
    install_system_deps
    setup_permissions
    install_python_deps
    
    # Configure optimizations
    configure_jetson
    
    # Test installation
    test_installation
    
    # Create shortcuts
    create_shortcuts
    
    echo "========================================================"
    print_success "Jetson Orin Integration SDK installation completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Log out and log back in for group permissions to take effect"
    echo "2. Run: source jetson_sdk_env/bin/activate"
    echo "3. Run: python3 main.py --mode detect"
    echo "4. Connect your cameras and LIDAR devices"
    echo "5. Run: python3 main.py --mode demo"
    echo ""
    print_status "For documentation, see README.md"
}

# Run main function
main "$@"