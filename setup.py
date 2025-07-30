#!/usr/bin/env python3
"""
Setup script for Jetson Edge SDK
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Jetson Edge SDK for camera and laser range finder operations"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r') as f:
            return [line.strip() for line in f 
                   if line.strip() and not line.startswith('#')]
    return []

setup(
    name="jetson-edge-sdk",
    version="1.0.0",
    author="Jetson Edge SDK Team",
    author_email="support@jetson-edge-sdk.com",
    description="A simple SDK for camera and laser range finder operations on Jetson Nano Orin",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/jetson-edge-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'black>=21.0.0',
            'flake8>=3.9.0',
        ],
        'examples': [
            'matplotlib>=3.5.0',
        ],
        'jetson': [
            'jetson-stats',
        ]
    },
    entry_points={
        'console_scripts': [
            'jetson-edge-basic=examples.basic_usage:main',
            'jetson-edge-callbacks=examples.advanced_callbacks:main',
            'jetson-edge-obstacles=examples.obstacle_detection:main',
        ],
    },
    include_package_data=True,
    package_data={
        'jetson_edge_sdk': ['*.json'],
    },
    zip_safe=False,
    keywords="jetson nano orin camera lidar range finder sdk edge computing",
    project_urls={
        "Bug Reports": "https://github.com/your-org/jetson-edge-sdk/issues",
        "Source": "https://github.com/your-org/jetson-edge-sdk",
        "Documentation": "https://github.com/your-org/jetson-edge-sdk/blob/main/README.md",
    },
)