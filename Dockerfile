# Jetson Orin Integration SDK Dockerfile
# Based on NVIDIA JetPack runtime

FROM nvcr.io/nvidia/l4t-base:r35.2.1

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY camera.py .
COPY lidar.py .
COPY main.py .
COPY test_sdk.py .

# Create output directories
RUN mkdir -p output test_output sample_output

# Set permissions for device access
RUN usermod -a -G video,dialout root

# Create a non-root user for running the application
RUN useradd -m -s /bin/bash jetson && \
    usermod -a -G video,dialout jetson && \
    chown -R jetson:jetson /app

# Switch to non-root user
USER jetson

# Expose ports for potential web interface
EXPOSE 8080

# Set default command
CMD ["python3", "main.py"]