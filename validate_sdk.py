#!/usr/bin/env python3
"""
Jetson Orin SDK Validation Script

This script validates the SDK structure and code quality without requiring
external dependencies. It checks file structure, syntax, and basic functionality.

Author: Jetson Orin SDK
"""

import os
import sys
import ast
import json
from pathlib import Path
from datetime import datetime


def check_file_structure():
    """Check that all required files exist."""
    print("=== Checking File Structure ===")
    
    required_files = [
        'camera.py',
        'lidar.py', 
        'main.py',
        'requirements.txt',
        'README.md',
        'test_sdk.py',
        'Dockerfile',
        'docker-compose.yml',
        '.gitignore'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nMissing files: {missing_files}")
        return False
    else:
        print("\n✓ All required files present")
        return True


def check_python_syntax():
    """Check Python syntax of all .py files."""
    print("\n=== Checking Python Syntax ===")
    
    python_files = ['camera.py', 'lidar.py', 'main.py', 'test_sdk.py']
    syntax_errors = []
    
    for file in python_files:
        try:
            with open(file, 'r') as f:
                source = f.read()
            ast.parse(source)
            print(f"✓ {file} - Syntax OK")
        except SyntaxError as e:
            print(f"✗ {file} - Syntax Error: {e}")
            syntax_errors.append((file, str(e)))
        except Exception as e:
            print(f"✗ {file} - Error: {e}")
            syntax_errors.append((file, str(e)))
    
    if syntax_errors:
        print(f"\nSyntax errors found: {len(syntax_errors)}")
        return False
    else:
        print("\n✓ All Python files have valid syntax")
        return True


def check_requirements():
    """Check requirements.txt file."""
    print("\n=== Checking Requirements ===")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        if requirements and requirements[0]:
            print(f"✓ requirements.txt contains {len(requirements)} packages")
            for req in requirements:
                if req.strip():
                    print(f"  - {req.strip()}")
            return True
        else:
            print("✗ requirements.txt is empty")
            return False
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False


def check_readme():
    """Check README.md file."""
    print("\n=== Checking README ===")
    
    try:
        with open('README.md', 'r') as f:
            content = f.read()
        
        # Check for key sections
        sections = [
            '## Features',
            '## Installation', 
            '## Usage',
            '## Configuration',
            '## Troubleshooting'
        ]
        
        missing_sections = []
        for section in sections:
            if section in content:
                print(f"✓ {section}")
            else:
                print(f"✗ {section} - MISSING")
                missing_sections.append(section)
        
        if missing_sections:
            print(f"\nMissing README sections: {missing_sections}")
            return False
        else:
            print("\n✓ README contains all required sections")
            return True
    except Exception as e:
        print(f"✗ Error reading README.md: {e}")
        return False


def check_docker_files():
    """Check Docker configuration files."""
    print("\n=== Checking Docker Configuration ===")
    
    # Check Dockerfile
    try:
        with open('Dockerfile', 'r') as f:
            dockerfile = f.read()
        
        if 'FROM nvcr.io/nvidia/l4t-base' in dockerfile:
            print("✓ Dockerfile uses correct base image")
        else:
            print("✗ Dockerfile missing correct base image")
            return False
        
        if 'COPY requirements.txt' in dockerfile:
            print("✓ Dockerfile copies requirements.txt")
        else:
            print("✗ Dockerfile missing requirements.txt copy")
            return False
        
        if 'CMD ["python3", "main.py"]' in dockerfile:
            print("✓ Dockerfile has correct CMD")
        else:
            print("✗ Dockerfile missing correct CMD")
            return False
        
    except Exception as e:
        print(f"✗ Error reading Dockerfile: {e}")
        return False
    
    # Check docker-compose.yml
    try:
        with open('docker-compose.yml', 'r') as f:
            compose = f.read()
        
        if 'jetson-sdk:' in compose:
            print("✓ docker-compose.yml has main service")
        else:
            print("✗ docker-compose.yml missing main service")
            return False
        
        if '/dev/video0' in compose:
            print("✓ docker-compose.yml mounts camera devices")
        else:
            print("✗ docker-compose.yml missing camera device mounts")
            return False
        
    except Exception as e:
        print(f"✗ Error reading docker-compose.yml: {e}")
        return False
    
    return True


def check_code_quality():
    """Check basic code quality metrics."""
    print("\n=== Checking Code Quality ===")
    
    python_files = ['camera.py', 'lidar.py', 'main.py']
    total_lines = 0
    total_functions = 0
    total_classes = 0
    
    for file in python_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
            
            # Count lines
            lines = len(content.split('\n'))
            total_lines += lines
            
            # Parse AST to count functions and classes
            tree = ast.parse(content)
            
            functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            
            total_functions += functions
            total_classes += classes
            
            print(f"✓ {file}: {lines} lines, {functions} functions, {classes} classes")
            
        except Exception as e:
            print(f"✗ {file}: Error analyzing - {e}")
    
    print(f"\nTotal: {total_lines} lines, {total_functions} functions, {total_classes} classes")
    
    # Basic quality checks
    if total_lines > 100:
        print("✓ Sufficient code volume")
    else:
        print("✗ Insufficient code volume")
        return False
    
    if total_functions > 10:
        print("✓ Good function coverage")
    else:
        print("✗ Limited function coverage")
        return False
    
    if total_classes > 3:
        print("✓ Good class structure")
    else:
        print("✗ Limited class structure")
        return False
    
    return True


def generate_validation_report():
    """Generate a comprehensive validation report."""
    print("=== Jetson Orin SDK Validation Report ===")
    print(f"Generated: {datetime.now().isoformat()}")
    
    checks = [
        ("File Structure", check_file_structure),
        ("Python Syntax", check_python_syntax),
        ("Requirements", check_requirements),
        ("README", check_readme),
        ("Docker Configuration", check_docker_files),
        ("Code Quality", check_code_quality)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n=== Validation Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{check_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 SDK validation successful! Ready for deployment.")
        return True
    else:
        print("⚠ Some validation checks failed. Review the issues above.")
        return False


def create_sample_output():
    """Create sample output files for demonstration."""
    print("\n=== Creating Sample Output ===")
    
    # Create output directories
    Path("output").mkdir(exist_ok=True)
    Path("test_output").mkdir(exist_ok=True)
    Path("sample_output").mkdir(exist_ok=True)
    
    # Sample hardware detection
    sample_hardware = {
        "timestamp": datetime.now().isoformat(),
        "cameras": [
            {
                "id": "usb_0",
                "type": "usb",
                "device_id": 0,
                "width": 640,
                "height": 480,
                "fps": 30,
                "description": "USB Camera 0"
            }
        ],
        "lidars": [
            {
                "id": "usb_ttyUSB0",
                "type": "usb",
                "device_path": "/dev/ttyUSB0",
                "baudrate": 115200,
                "description": "USB LIDAR /dev/ttyUSB0 @ 115200"
            }
        ],
        "total_devices": 2
    }
    
    # Sample capture summary
    sample_capture = {
        "capture_duration": 10.0,
        "capture_interval": 2.0,
        "total_captures": 5,
        "camera_captures": 5,
        "lidar_captures": 5,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
    
    # Save sample files
    with open("sample_output/hardware_detection.json", "w") as f:
        json.dump(sample_hardware, f, indent=2)
    
    with open("sample_output/capture_summary.json", "w") as f:
        json.dump(sample_capture, f, indent=2)
    
    print("✓ Sample output files created")
    print("  - sample_output/hardware_detection.json")
    print("  - sample_output/capture_summary.json")


if __name__ == "__main__":
    # Run validation
    success = generate_validation_report()
    
    # Create sample output
    create_sample_output()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)